import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from discussion.routing import websocket_urlpatterns as discussion_ws
from gramafication.routing import websocket_urlpatterns as gamification_ws
from .middleware import JWTAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                discussion_ws + gamification_ws
            )
        )
    ),
})
