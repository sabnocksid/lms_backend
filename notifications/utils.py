# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

async def send_realtime_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    payload = {
        "id": notification.id,
        "verb": notification.verb,
        "actor": notification.actor.get_full_name() if notification.actor else "System",
        "actor_id": notification.actor.id if notification.actor else None,
        "target_course": notification.target_course.name if notification.target_course else None,
        "target_course_id": notification.target_course.id if notification.target_course else None,
        "read": notification.read,
        "timestamp": notification.timestamp.isoformat(),
    }

    # Send to personal group: notifications_123
    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.recipient.id}",
        {
            "type": "send_notification",
            "notification": payload
        }
    )