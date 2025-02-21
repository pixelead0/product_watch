import uuid

from django.db import models

from core.models import BaseModel
from products.models import Product


class Visit(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="visits")
    ip_hash = models.CharField(max_length=64)
    user_agent = models.TextField(null=True, blank=True)
    session_id = models.CharField(max_length=36, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(null=True, blank=True)  # Duration in seconds

    def __str__(self) -> str:
        return f"Visit to {self.product} at {self.timestamp}"


class VisitSession(BaseModel):
    session_id = models.CharField(max_length=36, unique=True)
    first_visit_time = models.DateTimeField(auto_now_add=True)
    last_visit_time = models.DateTimeField(auto_now=True)
    visit_count = models.IntegerField(default=1)

    def __str__(self) -> str:
        return f"Session {self.session_id} with {self.visit_count} visits"


class ProductAnalytics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)
    total_visits = models.BigIntegerField(default=0)
    unique_visitors = models.BigIntegerField(default=0)
    avg_duration = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    daily_stats = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"Analytics for {self.product}"
