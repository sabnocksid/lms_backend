import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import DiscussionThread, DiscussionPost
from django.contrib.auth import get_user_model

User = get_user_model()

class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"discussion_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify others that a user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": "join",
                "username": self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous",
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Notify others that a user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": "leave",
                "username": self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous",
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "message":
            await self.handle_message(data)
        elif event_type == "history":
            await self.handle_history(data)
        elif event_type == "user_event":
            await self.handle_user_event(data)
        else:
            await self.send(json.dumps({"error": "Invalid event type"}))

    async def handle_message(self, data):
        message = data.get("message")
        username = self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        # Optional: persist message if thread exists
        try:
            thread = await self.get_thread(self.room_name)
            if thread and self.scope["user"].is_authenticated:
                await self.save_message(thread, self.scope["user"], message)
        except Exception as e:
            print("Message save failed:", e)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
                "timestamp": timestamp,
            }
        )

    async def handle_history(self, data):
        await self.send(json.dumps({
            "type": "history",
            "messages": [],
        }))

    async def handle_user_event(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": data.get("event"),
                "username": data.get("username"),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "username": event["username"],
            "timestamp": event["timestamp"],
        }))

    async def user_event(self, event):
        await self.send(json.dumps({
            "type": "user_event",
            "event": event["event"],
            "username": event["username"],
        }))

    @staticmethod
    async def get_thread(thread_id):
        try:
            return await DiscussionThread.objects.aget(pk=int(thread_id))
        except Exception:
            return None

    @staticmethod
    async def save_message(thread, user, content):
        await DiscussionPost.objects.acreate(
            thread=thread,
            creator=user,
            content=content
        )
