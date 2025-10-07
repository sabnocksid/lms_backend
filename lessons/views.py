from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Lesson, Chapter, ChapterProgress
from .serializers import LessonSerializer, ChapterSerializer, ChapterProgressSerializer


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


class ChapterProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ChapterProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChapterProgress.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        chapter = Chapter.objects.get(pk=pk)
        progress, _ = ChapterProgress.objects.get_or_create(user=request.user, chapter=chapter)
        progress.mark_completed()
        return Response({"status": "completed"})