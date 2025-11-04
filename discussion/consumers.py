import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import DiscussionThread, DiscussionPost

User = get_user_model()

class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'discussion_{self.thread_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        history = await self.get_thread_history(self.thread_id)
        await self.send(json.dumps({
            "type": "history",
            "messages": history
        }))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": "join",
                "username": self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Announce leave
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_event",
                "event": "leave",
                "username": self.scope["user"].username if self.scope["user"].is_authenticated else "Anonymous"
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "message":
            content = data.get("content")
            user = self.scope["user"]
            saved_message = await self.save_message(user, self.thread_id, content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": saved_message,
                }
            )

        elif msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "username": self.scope["user"].username,
                }
            )

    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "message",
            "message": event["message"]
        }))

    async def user_event(self, event):
        await self.send(json.dumps({
            "type": "user_event",
            "event": event["event"],
            "username": event["username"]
        }))

    async def typing_event(self, event):
        await self.send(json.dumps({
            "type": "typing",
            "username": event["username"]
        }))

    @database_sync_to_async
    def save_message(self, user, thread_id, content):
        thread = DiscussionThread.objects.get(id=thread_id)
        post = DiscussionPost.objects.create(
            creator=user,
            thread=thread,
            content=content
        )
        return {
            "id": post.id,
            "creator": post.creator.username,
            "content": post.content,
            "created_at": str(post.created_at)
        }

    @database_sync_to_async
    def get_thread_history(self, thread_id):
        posts = DiscussionPost.objects.filter(thread_id=thread_id).order_by("created_at")
        return [
            {
                "id": p.id,
                "creator": p.creator.username,
                "content": p.content,
                "created_at": str(p.created_at)
            }
            for p in posts
        ]
