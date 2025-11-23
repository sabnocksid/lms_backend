from celery import shared_task
from .models import Notification
from .utils import send_realtime_notification
import logging

logger = logging.getLogger(__name__)

@shared_task
def notify_user_task(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        send_realtime_notification(notification)
        logger.info(f"Notification sent: {notification.verb} -> {notification.recipient}")
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
