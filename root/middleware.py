import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        self.scope["user"] = None
        subprotocols = self.scope.get("subprotocols", [])
        if len(subprotocols) == 2 and subprotocols[0] == "Bearer":
            token = subprotocols[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                self.scope["user"] = await database_sync_to_async(User.objects.get)(id=payload["user_id"])
            except Exception:
                self.scope["user"] = None
        inner = self.inner(self.scope)
        return await inner(receive, send)
