import os
import uuid
import mimetypes
import tempfile

from django.conf import settings
from django.http import FileResponse, Http404

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Course, Lesson, Video, Enrollment
from .serializers import (
    CourseSerializer,
    LessonSerializer,
    VideoSerializer,
    EnrollmentSerializer,

)
from rest_framework.permissions import IsAuthenticated
from django.core.files import File
from utils.aes_crypto import encrypt_stream_for_user, decrypt_file_for_user


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user

class IsEnrolledOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return Enrollment.objects.filter(user=request.user, course=obj.lesson.course).exists()


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.select_related("lesson__course").all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        video_file = request.FILES.get("video_file")
        if not video_file:
            return Response({"detail": "No video_file provided."}, status=status.HTTP_400_BAD_REQUEST)

        enc_dir = os.path.join(settings.MEDIA_ROOT, "encrypted_videos")
        os.makedirs(enc_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex
        enc_filename = f"enc_{unique_id}_{video_file.name}"
        enc_path = os.path.join(enc_dir, enc_filename)

        try:
            encrypt_stream_for_user(request.user, video_file, enc_path)
        except Exception as e:
            return Response({"detail": f"Encryption failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with open(enc_path, 'rb') as f:
            django_file = File(f, name=enc_filename)
            data = {
                "title": request.data.get("title"),
                "lesson": request.data.get("lesson"),
                "video_file": django_file,
            }

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def stream(self, request, pk=None):
        """Stream decrypted video for enrolled users or admin"""
        video = self.get_object()
        enc_path = os.path.join(settings.MEDIA_ROOT, video.video_file.name)

        if not os.path.exists(enc_path):
            raise Http404("Encrypted video not found.")

        with tempfile.NamedTemporaryFile(delete=False) as tmp_out:
            tmp_output_path = tmp_out.name

        try:
            # Decrypt into temp file
            decrypt_file_for_user(request.user, enc_path, tmp_output_path)

            mime_type, _ = mimetypes.guess_type(video.video_file.name)
            response = FileResponse(open(tmp_output_path, "rb"), content_type=mime_type or "application/octet-stream")
            response["Content-Disposition"] = f'inline; filename="{os.path.basename(video.video_file.name)}"'
            return response
        finally:
            # Remove temp file after request finishes
            request.add_finished_callback(lambda *a, path=tmp_output_path: os.remove(path))



class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Enrollment.objects.all()
        return Enrollment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        user = self.request.user
        if Enrollment.objects.filter(course=course, user=user).exists():
            raise serializers.ValidationError("Already enrolled in this course.")
        serializer.save(user=user)

    @action(detail=False, methods=["get"])
    def my(self, request):
        qs = Enrollment.objects.filter(user=request.user)
        return Response(self.get_serializer(qs, many=True).data)
