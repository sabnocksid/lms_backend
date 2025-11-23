import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from root.middleware import JWTAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django_asgi_app = get_asgi_application()

from discussion.routing import websocket_urlpatterns as discussion_ws
from gramafication.routing import websocket_urlpatterns as notifications_ws

all_ws = discussion_ws + notifications_ws

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(all_ws)
        )
    ),
})
