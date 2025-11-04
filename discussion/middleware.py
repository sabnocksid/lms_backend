# discussion/middleware.py
import jwt
from django.conf import settings
from channels.db import database_sync_to_async
from accounts.models import CustomUser

@database_sync_to_async
def get_user_from_payload(payload):
    return CustomUser.objects.get(id=payload["user_id"])

class JWTAuthMiddleware:


    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)

class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = scope
        self.inner = inner

    async def __call__(self, receive, send):
        query_string = self.scope.get("query_string", b"").decode()
        token = None
        for param in query_string.split("&"):
            if param.startswith("token="):
                token = param.split("=")[1]
                break

        self.scope["user"] = None
        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                self.scope["user"] = await get_user_from_payload(payload)
            except Exception:
                self.scope["user"] = None

        inner = self.inner(self.scope)
        return await inner(receive, send)
