from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(notification):

    user = notification.recipient
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.id}",  
        {
            "type": "send_notification",  
            "notification": {
                "id": notification.id,
                "verb": notification.verb,
                "actor": str(notification.actor) if notification.actor else None,
                "target": str(notification.target_course) if hasattr(notification, "target_course") else None,
                "timestamp": str(notification.timestamp),
            }
        }
    )
