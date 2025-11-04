import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import DiscussionThread, DiscussionPost

User = get_user_model()

class DiscussionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'discussion_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            "type": "system",
            "message": f"Joined thread {self.room_name}"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("type")

        if action == "message":
            await self.create_message(data)
        elif action == "edit":
            await self.edit_message(data)
        elif action == "delete":
            await self.delete_message(data)
        elif action == "history":
            await self.load_history()


    async def create_message(self, data):
        thread = await self.get_thread(self.room_name)
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.send_error("Auth required to post")

        message = await self.save_post(thread, user, data.get("content"), data.get("parent"))
        payload = {
            "type": "new_message",
            "message": message
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def edit_message(self, data):
        post_id = data.get("post_id")
        content = data.get("content")
        message = await self.update_post(post_id, self.scope["user"], content)

        await self.channel_layer.group_send(self.room_group_name, {
            "type": "update_message",
            "message": message
        })

    async def delete_message(self, data):
        post_id = data.get("post_id")
        await self.remove_post(post_id, self.scope["user"])
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "delete_message",
            "post_id": post_id
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
        return DiscussionThread.objects.filter(pk=room_name).first()

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
