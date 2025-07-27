from rest_framework import generics
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework.permissions import AllowAny
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import login
from rest_framework import generics, status
from django.contrib.auth import login
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)  

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
    

        return Response({
            "message": "Login successful",
            "username": user.username,
            "role": request.user.role,
            "tokens": {
                "refresh": str(refresh),
                "access": str(access),
            }
        }, status=status.HTTP_200_OK)