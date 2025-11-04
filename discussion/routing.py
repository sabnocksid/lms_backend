from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from .consumers import DiscussionConsumer
from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter([
            path("ws/discussion/<room_name>/", DiscussionConsumer.as_asgi()),
        ])
    ),
})
