from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def send_realtime_notification(notification):
    channel_layer = get_channel_layer()
    group_name = f"notifications_{notification.recipient.id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "notification": {
                "id": notification.id,
                "verb": notification.verb,
                "actor": str(notification.actor) if notification.actor else None,
                "target": str(notification.target_course) if hasattr(notification, "target_course") else None,
                "timestamp": str(notification.timestamp)
            }
        }
    )
