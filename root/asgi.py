import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

from root.middleware import JWTAuthMiddleware  # your JWT middleware
from discussion.routing import websocket_urlpatterns as discussion_ws
from notifications.routing import websocket_urlpatterns as notification_ws

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                discussion_ws + notification_ws
            )
        )
    ),
})
