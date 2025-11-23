from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.tokens import UntypedToken
from jwt import decode as jwt_decode

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        query_string = parse_qs(scope["query_string"].decode())
        token_list = query_string.get("token")

        scope["user"] = AnonymousUser()

        if token_list:
            token = token_list[0]

            try:
                UntypedToken(token)
                decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await database_sync_to_async(User.objects.get)(id=decoded["user_id"])
                scope["user"] = user
            except Exception:
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
