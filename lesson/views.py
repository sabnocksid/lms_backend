from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Lesson
from .serializers import LessonCreateUpdateSerializer, LessonDetailSerializer, LessonListSerializer

from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def generate_key_from_user(user):
    password = str(user.id).encode() 
    salt = b'static_salt_1234'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

def encrypt_video_file(file_path, user):
    key = generate_key_from_user(user)
    fernet = Fernet(key)
    with open(file_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(file_path, "wb") as f:
        f.write(encrypted)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LessonCreateUpdateSerializer
        elif self.action == "list":
            return LessonListSerializer
        return LessonDetailSerializer

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)

        if instance.video_file:
            encrypt_video_file(instance.video_file.path, self.request.user)
        
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.video_file:
            encrypt_video_file(instance.video_file.path, instance.created_by)
        return instance

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"success": True, "message": "Lesson created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"success": True, "message": "Lesson updated successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Lesson deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
