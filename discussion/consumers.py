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
        logger.info(f"WebSocket connection attempt")
        
        user = self.scope.get("user")
        logger.info(f"User: {user}, Authenticated: {getattr(user, 'is_authenticated', False)}")
        
        # Reject unauthenticated users
        if not user or not user.is_authenticated:
            logger.warning("Unauthenticated connection attempt rejected")
            await self.close(code=4001)
            return
        
        # Get room name and convert to integer (thread ID)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'discussion_{self.room_name}'
        
        # Verify thread exists
        thread = await self.get_thread(self.room_name)
        if not thread:
            logger.warning(f"Thread {self.room_name} not found")
            await self.close(code=4004)
            return
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        logger.info(f"User {user.username} connected to thread {self.room_name}")
        
        # Send welcome message
        await self.send(json.dumps({
            "type": "system",
            "message": f"Joined thread {self.room_name}"
        }))

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: {close_code}")
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("type")
            
            logger.info(f"Received action: {action}")

            if action == "message":
                await self.create_message(data)
            elif action == "edit":
                await self.edit_message(data)
            elif action == "delete":
                await self.delete_message(data)
            elif action == "history":
                await self.load_history()
            else:
                await self.send_error(f"Unknown action: {action}")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send_error(str(e))

    async def create_message(self, data):
        thread = await self.get_thread(self.room_name)
        user = self.scope["user"]
        
        if not thread:
            return await self.send_error("Thread not found")
        
        if not user.is_authenticated:
            return await self.send_error("Auth required to post")

        content = data.get("content")
        if not content:
            return await self.send_error("Content is required")

        message = await self.save_post(thread, user, content, data.get("parent"))
        payload = {
            "type": "new_message",
            "message": message
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def edit_message(self, data):
        post_id = data.get("post_id")
        content = data.get("content")
        
        if not post_id or not content:
            return await self.send_error("post_id and content required")
        
        try:
            message = await self.update_post(post_id, self.scope["user"], content)
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "update_message",
                "message": message
            })
        except Exception as e:
            await self.send_error(str(e))

    async def delete_message(self, data):
        post_id = data.get("post_id")
        if not post_id:
            return await self.send_error("post_id required")
        
        try:
            await self.remove_post(post_id, self.scope["user"])
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "delete_message",
                "post_id": post_id
            })
        except Exception as e:
            await self.send_error(str(e))

    async def load_history(self):
        thread = await self.get_thread(self.room_name)
        if not thread:
            return await self.send_error("Thread not found")
        
        messages = await self.get_thread_messages(thread)
        await self.send(json.dumps({
            "type": "history",
            "messages": messages
        }))

    @database_sync_to_async
    def get_thread(self, room_name):
        try:
            # Convert room_name to integer if it's a thread ID
            thread_id = int(room_name)
            return DiscussionThread.objects.filter(pk=thread_id).first()
        except (ValueError, TypeError):
            return None

    @database_sync_to_async
    def save_post(self, thread, user, content, parent_id=None):
        parent = DiscussionPost.objects.filter(pk=parent_id).first() if parent_id else None
        post = DiscussionPost.objects.create(
            thread=thread,
            creator=user,
            content=content,
            parent=parent
        )
        return {
            "id": post.id,
            "creator": user.username,
            "content": content,
            "parent": parent_id,
            "created_at": post.created_at.isoformat(),
        }

    @database_sync_to_async
    def update_post(self, post_id, user, content):
        post = DiscussionPost.objects.get(pk=post_id, creator=user)
        post.content = content
        post.save()
        return {
            "id": post.id,
            "creator": user.username,
            "content": post.content,
            "updated": True,
        }

    @database_sync_to_async
    def remove_post(self, post_id, user):
        DiscussionPost.objects.filter(pk=post_id, creator=user).delete()

    @database_sync_to_async
    def get_thread_messages(self, thread):
        posts = DiscussionPost.objects.filter(thread=thread).select_related("creator").order_by("created_at")
        return [
            {
                "id": post.id,
                "creator": post.creator.username,
                "content": post.content,
                "parent": post.parent_id,
                "created_at": post.created_at.isoformat(),
            } for post in posts
        ]

    async def new_message(self, event):
        await self.send(json.dumps(event))

    async def update_message(self, event):
        await self.send(json.dumps(event))

    async def delete_message(self, event):
        await self.send(json.dumps(event))

    async def send_error(self, message):
        await self.send(json.dumps({"type": "error", "message": message}))