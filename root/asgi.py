import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")  

import django
django.setup() 

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from discussion.routing import websocket_urlpatterns
from gramafication.routing import websocket_urlpatterns
from .middleware import JWTAuthMiddleware

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,  
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})




application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            gramafication.routing.websocket_urlpatterns
        )
    ),
})