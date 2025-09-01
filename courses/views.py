from rest_framework import viewsets, permissions
from .models import Category, Lesson, LessonResource, LessonProgress, LessonReview
from .serializers import (
    CategorySerializer,
    LessonSerializer,
    LessonResourceSerializer,
    LessonProgressSerializer,
    LessonReviewSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
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


class LessonReviewViewSet(viewsets.ModelViewSet):
    queryset = LessonReview.objects.all()
    serializer_class = LessonReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
