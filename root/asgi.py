import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

django_asgi_app = get_asgi_application()

from root.middleware import JWTAuthMiddleware

def get_ws_urlpatterns():
    from discussion.routing import websocket_urlpatterns as discussion_ws
    from gramafication.routing import websocket_urlpatterns as notifications_ws
    return discussion_ws + notifications_ws 

all_ws = get_ws_urlpatterns()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(all_ws)
        )
    ),
})
