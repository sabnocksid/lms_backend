from django.urls import re_path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]


# from django.urls import re_path
# from .consumers import DiscussionConsumer

# websocket_urlpatterns = [
#     re_path(r'ws/discussion/(?P<room_name>\d+)/$', DiscussionConsumer.as_asgi()),
# ]
