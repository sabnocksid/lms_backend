from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Lesson, Chapter, ChapterProgress
from .serializers import LessonDetailSerializer, ChapterSerializer, ChapterProgressSerializer
from django.utils import timezone


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all().order_by("-created_at")
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def complete_and_next(self, request, pk=None):
        current_chapter = self.get_object()
        progress, _ = ChapterProgress.objects.get_or_create(user=request.user, chapter=current_chapter)
        progress.mark_completed()

        next_chapter = (
            Chapter.objects
            .filter(lesson=current_chapter.lesson, id__gt=current_chapter.id)
            .order_by("id")
            .first()
        )

        if not next_chapter:
            return Response({"status": "completed_all", "message": "You finished all chapters!"})

        serializer = self.get_serializer(next_chapter, context={"request": request})
        return Response({"status": "next_chapter", "chapter": serializer.data})
