import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from notifications.utils import serialize_notification  # We'll define this next

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send unread count
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": count
        }))

        # Send all unread notifications
        unread_notifications = await self.get_unread_notifications()
        for notif in unread_notifications:
            await self.send(text_data=json.dumps(notif))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["notification"]))

    @database_sync_to_async
    def get_unread_count(self):
        return self.user.notifications.filter(read=False).count()

    @database_sync_to_async
    def get_unread_notifications(self):
        return [serialize_notification(n) for n in self.user.notifications.filter(read=False)]
