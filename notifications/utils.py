# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(notification):
    """
    This function sends the notification to the user's WebSocket
    Called from Celery task
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Channel layer not available!")
        return

    payload = {
        "id": notification.id,
        "verb": notification.verb,
        "actor": notification.actor.get_full_name() if notification.actor else "System",
        "actor_id": notification.actor.id if notification.actor else None,
        "target_course": notification.target_course.name if notification.target_course else None,
        "target_course_id": notification.target_course.id if notification.target_course else None,
        "timestamp": notification.timestamp.isoformat(),
        "read": notification.read,
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{notification.recipient.id}",
            {
                "type": "send_notification",  
                "notification": payload
            }
        )
        print(f"WebSocket sent to user {notification.recipient.id}")
    except Exception as e:
        print(f"WebSocket send failed: {e}")