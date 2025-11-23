# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_realtime_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    # SAFELY get actor name
    actor_name = "System"
    if notification.actor:
        if hasattr(notification.actor, 'get_full_name') and callable(getattr(notification.actor, 'get_full_name')):
            actor_name = notification.actor.get_full_name() or notification.actor.username
        elif hasattr(notification.actor, 'full_name'):
            actor_name = notification.actor.full_name or notification.actor.username
        else:
            actor_name = notification.actor.username or "User"

    payload = {
        "id": notification.id,
        "verb": notification.verb,
        "actor": actor_name,
        "actor_id": notification.actor.id if notification.actor else None,
        "target_course": notification.target_course.name if notification.target_course else None,
        "target_course_id": notification.target_course.id if notification.target_course else None,
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