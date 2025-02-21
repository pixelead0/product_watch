import re
from typing import Callable, Optional
from uuid import UUID

from django.http import HttpRequest, HttpResponse

from visits.service import VisitService


class VisitTrackingMiddleware:
    """
    Middleware to track visits to product pages
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        # Compile the regex for product detail URLs
        self.product_pattern = re.compile(r"^/api/products/([a-f0-9-]+)/?$")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip tracking for non-GET requests
        if request.method != "GET":
            return self.get_response(request)

        # Extract product ID from URL
        product_id = self._extract_product_id(request.path)

        if product_id:
            # Get client IP address
            ip_address = self._get_client_ip(request)
            # Get User-Agent
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            # Get session ID from cookie (or None if not available)
            session_id = request.COOKIES.get("visit_session_id")

            # Track visit
            visit = VisitService.track_visit(
                product_id=product_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
            )

            # Process the request
            response = self.get_response(request)

            # Set session cookie if not already set
            if not session_id:
                response.set_cookie(
                    "visit_session_id",
                    visit.session_id,
                    max_age=60 * 60 * 24 * 30,  # 30 days
                    httponly=True,
                )

            return response

        return self.get_response(request)

    def _extract_product_id(self, path: str) -> Optional[UUID]:
        """
        Extract product ID from URL path
        """
        match = self.product_pattern.match(path)
        if match:
            try:
                return UUID(match.group(1))
            except ValueError:
                return None
        return None

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get client IP address, respecting proxy headers
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Get the first IP in the list
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip
