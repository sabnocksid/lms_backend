from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    LessonViewSet,
    LessonResourceViewSet,
    LessonProgressViewSet,
    LessonReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'resources', LessonResourceViewSet)
router.register(r'progress', LessonProgressViewSet)
router.register(r'reviews', LessonReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
