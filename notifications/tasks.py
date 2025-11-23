# notifications/tasks.py
from celery import shared_task
from .models import Notification
from .utils import send_realtime_notification
import asyncio

@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_notification_task(self, notification_id):
    try:
        notification = Notification.objects.select_related('recipient', 'actor', 'target_course').get(id=notification_id)
        asyncio.run(send_realtime_notification(notification))
    except Notification.DoesNotExist:
        return  
    except Exception as exc:
        raise self.retry(exc=exc)