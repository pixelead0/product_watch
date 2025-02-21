from typing import Dict, Union
from uuid import UUID

from notifications.tasks import (
    generate_daily_report,
    notify_product_created,
    notify_product_updated,
)


class NotificationService:
    @staticmethod
    def notify_product_created(product_id: UUID) -> Dict[str, Union[bool, str]]:
        """
        Queue notification for a new product
        """
        # Add task to queue
        task = notify_product_created.delay(str(product_id))

        return {"success": True, "task_id": task.id, "message": "Notification queued"}

    @staticmethod
    def notify_product_updated(product_id: UUID, updated_by_id: UUID) -> Dict[str, Union[bool, str]]:
        """
        Queue notification for a product update
        """
        # Add task to queue
        task = notify_product_updated.delay(str(product_id), str(updated_by_id))

        return {"success": True, "task_id": task.id, "message": "Notification queued"}

    @staticmethod
    def generate_daily_report() -> Dict[str, Union[bool, str]]:
        """
        Queue task to generate and send daily report
        """
        # Add task to queue
        task = generate_daily_report.delay()

        return {"success": True, "task_id": task.id, "message": "Daily report generation queued"}
