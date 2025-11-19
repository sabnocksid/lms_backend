from django.urls import path
from .consumers import DiscussionConsumer

websocket_urlpatterns = [
    path("ws/discussion/<room_name>/", DiscussionConsumer.as_asgi()),
]