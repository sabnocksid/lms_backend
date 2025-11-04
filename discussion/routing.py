from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/discussion/(?P<room_name>\w+)/$', consumers.DiscussionConsumer.as_asgi()),
]
