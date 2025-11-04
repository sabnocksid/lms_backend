import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import DiscussionThread, DiscussionPost

User = get_user_model()
logger = logging.getLogger(__name__)

class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'discussion_{self.room_name}'

        thread = await self.get_thread(self.room_name)
        if not thread:
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            "type": "system",
            "message": f"Joined thread {self.room_name}"
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("type")

            if action == "message":
                await self.create_message(data)
            elif action == "history":
                await self.load_history()
            else:
                await self.send_error(f"Unknown action: {action}")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(str(e))

    async def create_message(self, data):
        thread = await self.get_thread(self.room_name)
        user = self.scope["user"]
        content = data.get("content")
        parent_id = data.get("parent")

        if not content:
            return await self.send_error("Content is required")

        message = await self.save_post(thread, user, content, parent_id)
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "new_message",
            "message": message
        })

    async def load_history(self):
        thread = await self.get_thread(self.room_name)
        messages = await self.get_thread_messages(thread)
        await self.send(json.dumps({
            "type": "history",
            "messages": messages
        }))

    @database_sync_to_async
    def get_thread(self, room_name):
        try:
            thread_id = int(room_name)
            return DiscussionThread.objects.filter(pk=thread_id).first()
        except:
            return None

    @database_sync_to_async
    def save_post(self, thread, user, content, parent_id=None):
        parent = DiscussionPost.objects.filter(pk=parent_id).first() if parent_id else None
        post = DiscussionPost.objects.create(thread=thread, creator=user, content=content, parent=parent)
        profile_image = getattr(getattr(user, 'profile', None), 'profile_image', None)

        return {
            "id": post.id,
            "creator": user.full_name,
            "creator_id": user.id,
            "profile_image": profile_image,
            "content": content,
            "parent": parent_id,
            "created_at": post.created_at.isoformat(),
            "current_user": True
        }

    @database_sync_to_async
    def get_thread_messages(self, thread):
        current_user = self.scope["user"]
        posts = DiscussionPost.objects.filter(thread=thread).select_related("creator").order_by("created_at")
        messages = []

        for post in posts:
            creator = post.creator
            profile_image = getattr(getattr(creator, 'profile', None), 'profile_image', None)
            messages.append({
                "id": post.id,
                "creator": creator.full_name,
                "creator_id": creator.id,
                "profile_image": profile_image,
                "content": post.content,
                "parent": post.parent_id,
                "created_at": post.created_at.isoformat(),
                "current_user": creator.id == current_user.id
            })
        return messages

    async def new_message(self, event):
        await self.send(json.dumps(event))

    async def send_error(self, message):
        await self.send(json.dumps({"type": "error", "message": message}))
