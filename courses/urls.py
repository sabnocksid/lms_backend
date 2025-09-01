from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    LessonViewSet,
    LessonSectionViewSet,
    LessonResourceViewSet,
    LessonProgressViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'sections', LessonSectionViewSet)
router.register(r'resources', LessonResourceViewSet)
router.register(r'progress', LessonProgressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
