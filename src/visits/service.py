import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

from products.models import Product
from visits.models import ProductAnalytics, Visit, VisitSession


class VisitService:
    @staticmethod
    def _hash_ip(ip: str) -> str:
        """
        Hash IP address for privacy
        """
        return hashlib.sha256(ip.encode()).hexdigest()

    @staticmethod
    def _get_or_create_session(session_id: Optional[str] = None) -> str:
        """
        Get existing session or create new one
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            VisitSession.objects.create(session_id=session_id)
        else:
            # Update existing session
            try:
                session = VisitSession.objects.get(session_id=session_id)
                session.last_visit_time = timezone.now()
                session.visit_count += 1
                session.save()
            except VisitSession.DoesNotExist:
                # Create new session if the previous one is not found
                VisitSession.objects.create(session_id=session_id)

        return session_id

    @classmethod
    def track_visit(
        cls,
        product_id: UUID,
        ip_address: str,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Visit:
        """
        Track a new visit to a product
        """
        ip_hash = cls._hash_ip(ip_address)
        session_id = cls._get_or_create_session(session_id)

        # Create visit record
        visit = Visit.objects.create(
            product_id=product_id, ip_hash=ip_hash, user_agent=user_agent, session_id=session_id
        )

        # Update analytics asynchronously (this would be better handled by Celery)
        cls.update_analytics(product_id)

        return visit

    @classmethod
    def update_visit_duration(cls, visit_id: UUID, duration: int) -> Optional[Visit]:
        """
        Update visit duration when user leaves the page
        """
        try:
            visit = Visit.objects.get(id=visit_id)
            visit.duration = duration
            visit.save()

            # Update analytics for average duration
            cls.update_analytics(visit.product_id)

            return visit
        except Visit.DoesNotExist:
            return None

    @staticmethod
    def get_visits_for_product(
        product_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Visit]:
        """
        Get visits for a specific product with optional date filtering
        """
        query = Visit.objects.filter(product_id=product_id)

        if start_date:
            # Asegurar que la fecha tenga timezone
            if not timezone.is_aware(start_date):
                start_date = timezone.make_aware(start_date)
            # Usar __gt en lugar de __gte para un filtrado más estricto
            query = query.filter(timestamp__gt=start_date)

        if end_date:
            if not timezone.is_aware(end_date):
                end_date = timezone.make_aware(end_date)
            query = query.filter(timestamp__lte=end_date)

        return list(query.order_by("-timestamp")[:limit])

    @staticmethod
    def get_unique_visitors_count(
        product_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Get count of unique visitors for a product
        """
        query = Visit.objects.filter(product_id=product_id)

        if start_date:
            query = query.filter(timestamp__gte=start_date)
        if end_date:
            query = query.filter(timestamp__lte=end_date)

        return query.values("ip_hash").distinct().count()

    @classmethod
    @transaction.atomic
    def update_analytics(cls, product_id: UUID) -> ProductAnalytics:
        """
        Update analytics for a product
        """
        # Get or create analytics
        analytics, created = ProductAnalytics.objects.get_or_create(product_id=product_id)

        # Update total visits
        total_visits = Visit.objects.filter(product_id=product_id).count()

        # Update unique visitors
        unique_visitors = Visit.objects.filter(product_id=product_id).values("ip_hash").distinct().count()

        # Update average duration (ignoring null durations)
        avg_duration = Visit.objects.filter(product_id=product_id, duration__isnull=False).aggregate(
            avg_duration=Avg("duration")
        )["avg_duration"]

        # Get daily stats for last 30 days
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        daily_visits = (
            Visit.objects.filter(product_id=product_id, timestamp__gte=thirty_days_ago)
            .extra(select={"date": "DATE(timestamp)"})
            .values("date")
            .annotate(count=Count("id"), unique_visitors=Count("ip_hash", distinct=True))
            .order_by("date")
        )

        # Convert QuerySet to dict for JSON storage
        daily_stats = [
            {"date": str(day["date"]), "count": day["count"], "unique_visitors": day["unique_visitors"]}
            for day in daily_visits
        ]

        # Update analytics
        analytics.total_visits = total_visits
        analytics.unique_visitors = unique_visitors
        analytics.avg_duration = avg_duration
        analytics.daily_stats = daily_stats
        analytics.save()

        return analytics

    @staticmethod
    def get_popular_products(limit: int = 5) -> List[Tuple[Product, Dict]]:
        """
        Get most popular products based on visit counts
        """
        # Get products with most visits in last 30 days
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        # Current period stats
        current_period_stats = (
            Visit.objects.filter(timestamp__gte=thirty_days_ago)
            .values("product_id")
            .annotate(
                total_visits=Count("id"),
                unique_visitors=Count("ip_hash", distinct=True),
            )
            .order_by("-total_visits")[:limit]
        )

        # Previous period stats for comparison
        previous_period_stats = (
            Visit.objects.filter(timestamp__gte=sixty_days_ago, timestamp__lt=thirty_days_ago)
            .values("product_id")
            .annotate(prev_total_visits=Count("id"))
            .order_by("-prev_total_visits")
        )

        # Convert to dict for easy lookup
        prev_stats_dict = {item["product_id"]: item["prev_total_visits"] for item in previous_period_stats}

        # Calculate percentage change and combine with product objects
        result = []
        for stat in current_period_stats:
            try:
                product = Product.objects.get(id=stat["product_id"])

                # Calculate percentage change
                prev_visits = prev_stats_dict.get(stat["product_id"], 0)
                if prev_visits > 0:
                    percentage_change = ((stat["total_visits"] - prev_visits) / prev_visits) * 100
                else:
                    percentage_change = 100.0  # New product with no previous visits

                result.append(
                    (
                        product,
                        {
                            "total_visits": stat["total_visits"],
                            "unique_visitors": stat["unique_visitors"],
                            "percentage_change": percentage_change,
                        },
                    )
                )
            except Product.DoesNotExist:
                # Skip if product no longer exists
                continue

        return result
