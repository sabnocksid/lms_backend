import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")  

import django
django.setup() 

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from discussion.routing import websocket_urlpatterns
from discussion.middleware import JWTAuthMiddleware
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})