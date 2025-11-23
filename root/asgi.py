import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

# Standard Django ASGI app for HTTP
django_asgi_app = get_asgi_application()

# Lazy import of JWT middleware
from root.middleware import JWTAuthMiddleware

# Lazy import routing inside ASGI to avoid early model import
def get_ws_urlpatterns():
    from discussion.routing import websocket_urlpatterns as discussion_ws
    from notifications.routing import websocket_urlpatterns as notifications_ws
    return discussion_ws + notifications_ws  # Combine safely

all_ws = get_ws_urlpatterns()

# ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(all_ws)
        )
    ),
})
