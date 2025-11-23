import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger("notifications_ws")

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthorized WS connection attempt")
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WS connected for user {self.user.id}")

        # Send existing notifications
        notifications = await self.get_user_notifications()
        for n in notifications:
            await self.send(text_data=json.dumps(n))
            logger.info(f"Sent existing notification: {n}")

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WS disconnected for user {self.user.id}, code {close_code}")

    async def receive(self, text_data):
        logger.info(f"WS message received from user {self.user.id}: {text_data}")

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["notification"]))
        logger.info(f"WS notification sent to user {self.user.id}: {event['notification']}")

    @database_sync_to_async
    def get_user_notifications(self):
        return [
            {
                "id": n.id,
                "verb": n.verb,
                "actor": str(n.actor) if n.actor else None,
                "target": str(n.target_course) if n.target_course else None,
                "timestamp": str(n.timestamp),
            }
            for n in self.user.notifications.all().order_by("-timestamp")
        ]
