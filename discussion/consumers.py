import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from gramafication.models import LearnerProfile
from .models import DiscussionThread, DiscussionPost
from lessons.utils.upload_minio import get_presigned_url

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
            elif action == "update":
                await self.update_message(data)
            elif action == "delete":
                await self.delete_message(data)
            else:
                await self.send_error(f"Unknown action: {action}")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            logger.exception("WebSocket error")
            await self.send_error(str(e))

    # ---------------------- CREATE ----------------------
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

    # ---------------------- UPDATE ----------------------
    async def update_message(self, data):
        post_id = data.get("id")
        new_content = data.get("content")

        if not post_id or not new_content:
            return await self.send_error("Message ID and new content required")

        user = self.scope["user"]
        updated_message = await self.update_post(post_id, user, new_content)

        if not updated_message:
            return await self.send_error("Update failed or permission denied")

        await self.channel_layer.group_send(self.room_group_name, {
            "type": "broadcast_updated_message",
            "message": updated_message
        })

    # ---------------------- DELETE ----------------------
    async def delete_message(self, data):
        post_id = data.get("id")

        if not post_id:
            return await self.send_error("Message ID required")

        user = self.scope["user"]
        deleted_id = await self.delete_post(post_id, user)

        if not deleted_id:
            return await self.send_error("Delete failed or permission denied")

        await self.channel_layer.group_send(self.room_group_name, {
            "type": "broadcast_deleted_message",
            "message": {"id": deleted_id}
        })

    # ---------------------- HISTORY ----------------------
    async def load_history(self):
        thread = await self.get_thread(self.room_name)
        if not thread:
            return await self.send_error("Thread not found")

        messages = await self.get_thread_messages(thread)
        await self.send_json({
            "type": "history",
            "messages": messages
        })

    # ---------------------- BROADCASTS ----------------------
    async def broadcast_new_message(self, event):
        await self.send_json({
            "type": "new_message",
            "message": event["message"]
        })

    async def broadcast_updated_message(self, event):
        await self.send_json({
            "type": "updated_message",
            "message": event["message"]
        })

    async def broadcast_deleted_message(self, event):
        await self.send_json({
            "type": "deleted_message",
            "message": event["message"]
        })

    @database_sync_to_async
    def get_thread(self, room_name):
        try:
            thread_id = int(room_name)
            return DiscussionThread.objects.filter(pk=thread_id).first()
        except (ValueError, TypeError):
            return None

    @database_sync_to_async
    def save_post(self, thread, user, content, parent_id=None):
        parent = DiscussionPost.objects.filter(pk=parent_id).first() if parent_id else None
        post = DiscussionPost.objects.create(thread=thread, creator=user, content=content, parent=parent)

        full_name, profile_image = self.get_user_display_info_sync(user)
        profile_image_url = get_presigned_url(profile_image) if profile_image else None

        return {
            "id": post.id,
            "creator": full_name,
            "creator_id": user.id,
            "profile_image": profile_image_url,
            "content": post.content,
            "parent": parent_id,
            "created_at": post.created_at.isoformat(),
            "current_user": True  
        }

    @database_sync_to_async
    def update_post(self, post_id, user, new_content):
        try:
            post = DiscussionPost.objects.get(pk=post_id)
            if post.creator != user:
                return None
            post.content = new_content
            post.save()

            full_name, profile_image = self.get_user_display_info_sync(user)
            profile_image_url = get_presigned_url(profile_image) if profile_image else None

            return {
                "id": post.id,
                "creator": full_name,
                "creator_id": user.id,
                "profile_image": profile_image_url,
                "content": post.content,
                "parent": post.parent_id,
                "created_at": post.created_at.isoformat(),
            }
        except DiscussionPost.DoesNotExist:
            return None

    @database_sync_to_async
    def delete_post(self, post_id, user):
        try:
            post = DiscussionPost.objects.get(pk=post_id)
            if post.creator != user:
                return None
            post.delete()
            return post_id
        except DiscussionPost.DoesNotExist:
            return None

    @database_sync_to_async
    def get_thread_messages(self, thread):
        current_user = self.scope["user"]
        posts = DiscussionPost.objects.filter(thread=thread).select_related("creator").order_by("created_at")
        messages = []

        for post in posts:
            creator = post.creator
            full_name, profile_image = self.get_user_display_info_sync(creator)
            profile_image_url = get_presigned_url(profile_image) if profile_image else None

            messages.append({
                "id": post.id,
                "creator": full_name,
                "creator_id": creator.id,
                "profile_image": profile_image_url,
                "content": post.content,
                "parent": post.parent_id,
                "created_at": post.created_at.isoformat(),
                "current_user": creator.id == getattr(current_user, "id", None),
            })
        return messages

    def get_user_display_info_sync(self, user):
        try:
            learner = getattr(user, "profile", None)
            if isinstance(learner, LearnerProfile):
                return learner.full_name, learner.profile_image
        except Exception:
            pass
        full_name = getattr(user, "full_name", None) or f"{user.first_name} {user.last_name}".strip() or user.username
        return full_name, None

    async def send_json(self, obj):
        await self.send(json.dumps(obj))

    async def send_error(self, message):
        await self.send_json({"type": "error", "message": message})
