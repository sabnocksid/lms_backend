import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["notification"]))

    @database_sync_to_async
    def create_notification_dict(self, notification):
        from .models import Notification
        return {
            "id": notification.id,
            "verb": notification.verb,
            "actor": str(notification.actor) if notification.actor else None,
            "target": str(notification.target_course) if hasattr(notification, "target_course") else None,
            "timestamp": str(notification.timestamp)
        }
