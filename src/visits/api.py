from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router

from auth.dependencies import get_admin_auth
from visits.schemas import PopularProductOut, ProductAnalyticsOut, VisitOut
from visits.service import VisitService

router = Router(tags=["visits"])
visit_service = VisitService()


@router.post("/track/{visit_id}", response={200: Dict[str, str], 404: Dict[str, str]})
def update_visit_duration(request: HttpRequest, visit_id: UUID, duration: int):
    """
    Update the duration of a visit when the user leaves the page.
    """
    visit = visit_service.update_visit_duration(visit_id, duration)
    if not visit:
        return 404, {"detail": "Visit not found"}
    return 200, {"detail": "Visit duration updated"}


@router.get("/product/{product_id}", auth=get_admin_auth(), response={200: List[VisitOut], 404: Dict[str, str]})
def get_product_visits(
    request: HttpRequest,
    product_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
):
    """
    Get visits for a specific product (admin only).
    """
    visits = visit_service.get_visits_for_product(product_id, start_date, end_date, limit)
    return 200, [VisitOut.from_orm(v) for v in visits]


@router.get(
    "/analytics/product/{product_id}", auth=get_admin_auth(), response={200: ProductAnalyticsOut, 404: Dict[str, str]}
)
def get_product_analytics(request: HttpRequest, product_id: UUID):
    """
    Get analytics for a specific product (admin only).
    """
    analytics = visit_service.update_analytics(product_id)
    if not analytics:
        return 404, {"detail": "Analytics not found"}

    # Convert daily_stats from JSON to list
    daily_stats = analytics.daily_stats

    return 200, ProductAnalyticsOut(
        product_id=product_id,
        total_visits=analytics.total_visits,
        unique_visitors=analytics.unique_visitors,
        avg_duration=analytics.avg_duration,
        last_updated=analytics.last_updated,
        daily_stats=daily_stats,
    )


@router.get("/popular", auth=get_admin_auth(), response=List[PopularProductOut])
def get_popular_products(request: HttpRequest, limit: int = 5):
    """
    Get most popular products based on visit counts (admin only).
    """
    popular_products = visit_service.get_popular_products(limit)

    return [
        PopularProductOut(
            product_id=product.id,
            name=product.name,
            total_visits=stats["total_visits"],
            unique_visitors=stats["unique_visitors"],
            percentage_change=stats["percentage_change"],
        )
        for product, stats in popular_products
    ]
