from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, ChapterViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r"lessons", LessonViewSet, basename="lessons")
router.register(r"chapters", ChapterViewSet, basename="chapters")

urlpatterns = [
    path("", include(router.urls)),
]