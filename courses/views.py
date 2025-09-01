from rest_framework import viewsets, permissions
from .models import Category, Lesson, LessonSection, LessonResource, LessonProgress
from .serializers import (
    CategorySerializer,
    LessonSerializer,
    LessonSectionSerializer,
    LessonResourceSerializer,
    LessonProgressSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LessonSectionViewSet(viewsets.ModelViewSet):
    queryset = LessonSection.objects.all()
    serializer_class = LessonSectionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LessonResourceViewSet(viewsets.ModelViewSet):
    queryset = LessonResource.objects.all()
    serializer_class = LessonResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LessonProgressViewSet(viewsets.ModelViewSet):
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
