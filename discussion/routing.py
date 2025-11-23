from django.urls import re_path
from .consumers import DiscussionConsumer

websocket_urlpatterns = [
    re_path(r'ws/discussion/(?P<thread_id>\d+)/$', DiscussionConsumer.as_asgi()),
]
