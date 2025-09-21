from rest_framework import viewsets, permissions
from .models import Lesson, Chapter
from .serializers import LessonSerializer, ChapterSerializer


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all().order_by("-created_at")
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all().order_by("-created_at")
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
