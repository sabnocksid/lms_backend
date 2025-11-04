from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/discussion/(?P<thread_id>\d+)/$", consumers.DiscussionConsumer.as_asgi()),
]
