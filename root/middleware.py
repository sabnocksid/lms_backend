from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Lazy imports
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser  # move here
        from rest_framework_simplejwt.tokens import UntypedToken
        from jwt import decode as jwt_decode
        from django.conf import settings
        import logging

        logger = logging.getLogger(__name__)
        User = get_user_model()

        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")
        scope["user"] = AnonymousUser()

        if token:
            try:
                validated_token = UntypedToken(token[0])
                decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
                user = await database_sync_to_async(User.objects.get)(id=decoded_data["user_id"])
                scope["user"] = user
            except Exception as e:
                logger.warning(f"JWTAuthMiddleware failed: {e}")
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
