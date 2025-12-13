import jwt
from channels.middleware import BaseMiddleware
from django.conf import settings
from urllib.parse import parse_qs

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser  # <-- moved inside

        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

                from django.contrib.auth import get_user_model  # <-- safe here
                User = get_user_model()

                user = await self.get_user(payload["user_id"], User)
                scope["user"] = user
            except Exception:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @staticmethod
    async def get_user(user_id, User):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def inner():
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        return await inner()
