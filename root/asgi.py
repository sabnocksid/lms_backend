# import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")  

# import django
# django.setup() 

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.security.websocket import AllowedHostsOriginValidator
# from discussion.routing import websocket_urlpatterns
# from gramafication.routing import websocket_urlpatterns
# from .middleware import JWTAuthMiddleware

# django_asgi_app = get_asgi_application()

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,  
#     "websocket": AllowedHostsOriginValidator(
#         JWTAuthMiddleware(
#             URLRouter(websocket_urlpatterns)
#         )
#     ),
# })



import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

import django
django.setup()  # must be first

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

# now safe to import your middleware and routing
from .middleware import JWTAuthMiddleware
from discussion.routing import websocket_urlpatterns as discussion_ws
from gramafication.routing import websocket_urlpatterns as gamification_ws

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(gamification_ws + discussion_ws)
        )
    ),
})

