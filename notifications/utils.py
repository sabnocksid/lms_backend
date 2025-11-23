from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    actor_name = getattr(notification.actor, 'get_full_name', lambda: None)() or \
                 getattr(notification.actor, 'full_name', None) or \
                 getattr(notification.actor, 'username', 'System')

    payload = {
        "id": notification.id,
        "verb": notification.verb,
        "actor": actor_name,
        "actor_id": notification.actor.id if notification.actor else None,
        "target_course": getattr(notification.target_course, 'name', None),
        "target_course_id": getattr(notification.target_course, 'id', None),
        "timestamp": notification.timestamp.isoformat(),
        "read": notification.read,
    }

    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.recipient.id}",
        {
            "type": "send_notification",
            "notification": payload
        }
    )
