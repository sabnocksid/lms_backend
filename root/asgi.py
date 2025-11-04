import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")  

import django
django.setup() 

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from discussion import routing
from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
})
