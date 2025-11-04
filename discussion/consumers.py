import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from gramafication.models import LearnerProfile
from .models import DiscussionThread, DiscussionPost

User = get_user_model()
logger = logging.getLogger(__name__)


class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"discussion_{self.room_name}"

        thread = await self.get_thread(self.room_name)
        if not thread:
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send_json({
            "type": "system",
            "message": f"Joined thread {self.room_name}"
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
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
            logger.exception("WebSocket error")
            await self.send_error(str(e))

    async def create_message(self, data):
        thread = await self.get_thread(self.room_name)
        user = self.scope["user"]
        content = data.get("content")
        parent_id = data.get("parent")

        if not thread:
            return await self.send_error("Thread not found")
        if not user.is_authenticated:
            return await self.send_error("Auth required to post")
        if not content:
            return await self.send_error("Content is required")

        message = await self.save_post(thread, user, content, parent_id)

        await self.channel_layer.group_send(self.room_group_name, {
            "type": "broadcast_new_message",
            "message": message
        })

    async def load_history(self):
        thread = await self.get_thread(self.room_name)
        if not thread:
            return await self.send_error("Thread not found")

        messages = await self.get_thread_messages(thread)
        await self.send_json({
            "type": "history",
            "messages": messages
        })

    async def broadcast_new_message(self, event):
        message = event.get("message", {})
        creator_id = message.get("creator_id")
        current_user_flag = (getattr(self.scope.get("user"), "id", None) == creator_id)

        msg_for_client = dict(message)
        msg_for_client["current_user"] = current_user_flag

        await self.send_json({
            "type": "new_message",
            "message": msg_for_client
        })

    @database_sync_to_async
    def get_thread(self, room_name):
        try:
            thread_id = int(room_name)
            return DiscussionThread.objects.filter(pk=thread_id).first()
        except (ValueError, TypeError):
            return None

    @database_sync_to_async
    def get_user_display_info(self, user):
        """Safely get name + image from either LearnerProfile or User."""
        try:
            learner = getattr(user, "profile", None)
            if isinstance(learner, LearnerProfile):
                return learner.full_name, learner.profile_image
        except Exception:
            pass

        # Fallback
        full_name = getattr(user, "full_name", None) or f"{user.first_name} {user.last_name}".strip() or user.username
        return full_name, None

    @database_sync_to_async
    def save_post(self, thread, user, content, parent_id=None):
        parent = DiscussionPost.objects.filter(pk=parent_id).first() if parent_id else None
        post = DiscussionPost.objects.create(thread=thread, creator=user, content=content, parent=parent)

        full_name, profile_image = self.get_user_display_info_sync(user)

        return {
            "id": post.id,
            "creator": full_name,
            "creator_id": user.id,
            "profile_image": profile_image,
            "content": post.content,
            "parent": parent_id,
            "created_at": post.created_at.isoformat(),
        }

    def get_user_display_info_sync(self, user):
        try:
            learner = getattr(user, "profile", None)
            if isinstance(learner, LearnerProfile):
                return learner.full_name, learner.profile_image
        except Exception:
            pass
        full_name = getattr(user, "full_name", None) or f"{user.first_name} {user.last_name}".strip() or user.username
        return full_name, None

    @database_sync_to_async
    def get_thread_messages(self, thread):
        current_user = self.scope["user"]
        posts = DiscussionPost.objects.filter(thread=thread).select_related("creator").order_by("created_at")
        messages = []

        for post in posts:
            creator = post.creator
            full_name, profile_image = self.get_user_display_info_sync(creator)

            messages.append({
                "id": post.id,
                "creator": full_name,
                "creator_id": creator.id,
                "profile_image": profile_image,
                "content": post.content,
                "parent": post.parent_id,
                "created_at": post.created_at.isoformat(),
                "current_user": creator.id == getattr(current_user, "id", None),
            })
        return messages

    async def send_json(self, obj):
        await self.send(json.dumps(obj))

    async def send_error(self, message):
        await self.send_json({"type": "error", "message": message})
