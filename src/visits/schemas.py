from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ninja import Schema


class VisitBase(Schema):
    product_id: UUID
    ip_hash: str
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    duration: Optional[int] = None


class VisitOut(VisitBase):
    id: UUID
    timestamp: datetime


class VisitSessionOut(Schema):
    session_id: str
    first_visit_time: datetime
    last_visit_time: datetime
    visit_count: int


class DailyVisitStats(Schema):
    date: str
    count: int
    unique_visitors: int


class ProductAnalyticsOut(Schema):
    product_id: UUID
    total_visits: int
    unique_visitors: int
    avg_duration: Optional[int] = None
    last_updated: datetime
    daily_stats: List[DailyVisitStats]


class PopularProductOut(Schema):
    product_id: UUID
    name: str
    total_visits: int
    unique_visitors: int
    percentage_change: float  # Change compared to previous period
