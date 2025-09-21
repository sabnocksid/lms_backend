from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, ChapterViewSet

router = DefaultRouter()
router.register(r"lessons", LessonViewSet, basename="lessons")
router.register(r"chapters", ChapterViewSet, basename="chapters")

urlpatterns = [
    path("api/", include(router.urls)),
]