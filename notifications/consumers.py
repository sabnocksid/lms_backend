# notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        unread_count = await self.get_unread_count(user)
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": unread_count
        }))

        recent = await self.get_recent_notifications(user)
        for notif in recent:
            await self.send(text_data=json.dumps(notif))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["notification"]))

    @database_sync_to_async
    def get_unread_count(self, user):
        return user.notifications.filter(read=False).count()

    @database_sync_to_async
    def get_recent_notifications(self, user):
        qs = user.notifications.select_related('actor', 'target_course').order_by('-timestamp')[:10]
        return [
            {
                "id": n.id,
                "verb": n.verb,
                "actor": n.actor.get_full_name() if n.actor else "System",
                "actor_id": n.actor.id if n.actor else None,
                "target_course": n.target_course.name if n.target_course else None,
                "target_course_id": n.target_course.id if n.target_course else None,
                "read": n.read,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in qs
        ]