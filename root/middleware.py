import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        query_string = scope.get("query_string", b"").decode()
        token = None
        
        if "token=" in query_string:
            token = query_string.split("token=")[1].split("&")[0]
        
        if not token:
            subprotocols = scope.get("subprotocols", [])
            if len(subprotocols) >= 2 and subprotocols[0] == "Bearer":
                token = subprotocols[1]

        if token:
            user = await self.get_user_from_token(token)
            if user:
                scope["user"] = user

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):

        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            user = User.objects.get(id=payload["user_id"])
            return user
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            return None
        



from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        if token:
            try:
                validated_token = UntypedToken(token[0])
                decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
                user = await database_sync_to_async(User.objects.get)(id=decoded_data["user_id"])
                scope["user"] = user
            except Exception:
                scope["user"] = None
        return await super().__call__(scope, receive, send)
