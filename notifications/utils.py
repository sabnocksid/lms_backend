from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def serialize_notification(notification):
    actor_name = getattr(notification.actor, 'get_full_name', lambda: None)() or \
                 getattr(notification.actor, 'full_name', None) or \
                 getattr(notification.actor, 'username', 'System')
    return {
        "type": "notification",
        "id": notification.id,
        "verb": notification.verb,
        "actor": actor_name,
        "actor_id": notification.actor.id if notification.actor else None,
        "target_course": getattr(notification.target_course, 'name', None),
        "target_course_id": getattr(notification.target_course, 'id', None),
        "timestamp": notification.timestamp.isoformat(),
        "read": notification.read,
    }

def send_realtime_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    payload = serialize_notification(notification)

    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.recipient.id}",
        {
            "type": "send_notification",  # matches consumer method
            "notification": payload
        }
    )
