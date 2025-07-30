# course/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Course, Lesson, Video, Enrollment
from .serializers import CourseSerializer, LessonSerializer, VideoSerializer, EnrollmentSerializer
from utils.aes_crypto import handle_video_upload
from django.conf import settings


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('video_file')
        if uploaded_file:
            filename = uploaded_file.name
            encrypted_path = handle_video_upload(uploaded_file, filename)
            relative_path = encrypted_path.replace('media/', '')

            data = request.data.copy()
            data['video_file'] = relative_path

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            video_url = request.build_absolute_uri(settings.MEDIA_URL + relative_path)

            response_data = serializer.data
            response_data['video_url'] = video_url

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
