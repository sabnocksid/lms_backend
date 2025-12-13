from celery import shared_task
from .models import Notification
from .utils import send_realtime_notification

@shared_task
def send_notification_task(notification_id):
    try:
        notification = Notification.objects.select_related(
            'recipient', 'actor', 'target_course'
        ).get(id=notification_id)
        send_realtime_notification(notification)
    except Notification.DoesNotExist:
        pass
