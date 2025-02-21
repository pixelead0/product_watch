import logging
from typing import Dict, List, Optional, Union
from uuid import UUID

import sendgrid
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.template.loader import render_to_string
from sendgrid.helpers.mail import Content, Email, Mail, To

from auth.models import User
from products.models import Product
from visits.service import VisitService

# Setup logging
logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="send_email_notification",
)
def send_email_notification(self, to_emails: List[str], subject: str, html_content: str) -> Dict[str, Union[bool, str]]:
    """
    Send email notification using SendGrid
    """
    try:
        sg_client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        from_email = Email(settings.NOTIFICATION_FROM_EMAIL)

        mail = Mail(
            from_email=from_email,
            subject=subject,
        )

        # Add multiple recipients
        for email in to_emails:
            mail.add_personalization(To(email))

        # Add email content
        mail.add_content(Content("text/html", html_content))

        # Send email
        response = sg_client.client.mail.send.post(request_body=mail.get())

        # Log response
        logger.info(f"Email sent to {to_emails} with status {response.status_code}")

        return {
            "success": response.status_code in [200, 201, 202],
            "status_code": response.status_code,
            "message": "Email sent successfully",
        }

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        # Retry the task
        raise self.retry(exc=e)


@shared_task(name="notify_product_created")
def notify_product_created(product_id: str) -> Dict[str, Union[bool, str]]:
    """
    Notify all admin users about a new product
    """
    try:
        # Get product
        product = Product.objects.get(id=product_id)

        # Get all admin users
        admin_users = User.objects.filter(is_admin=True)

        if not admin_users:
            return {"success": False, "message": "No admin users found to notify"}

        # Prepare email content
        subject = f"New Product Created: {product.name}"
        html_content = render_to_string(
            "emails/product_created.html",
            {
                "product": product,
            },
        )

        # Send email
        to_emails = [user.email for user in admin_users]
        send_email_notification.delay(to_emails, subject, html_content)

        return {"success": True, "message": f"Notification sent to {len(to_emails)} admin users"}

    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        return {"success": False, "message": f"Product {product_id} not found"}
    except Exception as e:
        logger.error(f"Failed to notify product creation: {str(e)}")
        return {"success": False, "message": str(e)}


@shared_task(name="notify_product_updated")
def notify_product_updated(product_id: str, updated_by_id: str) -> Dict[str, Union[bool, str]]:
    """
    Notify admin users about a product update
    """
    try:
        # Get product
        product = Product.objects.get(id=product_id)

        # Get analytics
        visit_service = VisitService()
        analytics = visit_service.update_analytics(product_id)

        # Get updated by user
        try:
            updated_by = User.objects.get(id=updated_by_id)
        except User.DoesNotExist:
            updated_by = None

        # Get all admin users except the one who updated
        admin_users = User.objects.filter(is_admin=True)
        if updated_by:
            admin_users = admin_users.exclude(id=updated_by_id)

        if not admin_users:
            return {"success": False, "message": "No admin users found to notify"}

        # Prepare email content
        subject = f"Product Updated: {product.name}"
        html_content = render_to_string(
            "emails/product_updated.html", {"product": product, "analytics": analytics, "updated_by": updated_by}
        )

        # Send email
        to_emails = [user.email for user in admin_users]
        send_email_notification.delay(to_emails, subject, html_content)

        return {"success": True, "message": f"Notification sent to {len(to_emails)} admin users"}

    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        return {"success": False, "message": f"Product {product_id} not found"}
    except Exception as e:
        logger.error(f"Failed to notify product update: {str(e)}")
        return {"success": False, "message": str(e)}


@shared_task(name="generate_daily_report")
def generate_daily_report() -> Dict[str, Union[bool, str]]:
    """
    Generate and send daily report to all admin users
    """
    try:
        # Get all products
        products = Product.objects.all()

        # Get popular products
        visit_service = VisitService()
        popular_products = visit_service.get_popular_products(limit=10)

        # Get all admin users
        admin_users = User.objects.filter(is_admin=True)

        if not admin_users:
            return {"success": False, "message": "No admin users found to notify"}

        # Prepare email content
        subject = "Daily Product Report"
        html_content = render_to_string(
            "emails/daily_report.html",
            {"products": products, "popular_products": popular_products, "total_products": products.count()},
        )

        # Send email
        to_emails = [user.email for user in admin_users]
        send_email_notification.delay(to_emails, subject, html_content)

        return {"success": True, "message": f"Daily report sent to {len(to_emails)} admin users"}

    except Exception as e:
        logger.error(f"Failed to generate daily report: {str(e)}")
        return {"success": False, "message": str(e)}
