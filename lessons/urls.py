from rest_framework.routers import DefaultRouter
from .views import LessonViewSet, ChapterViewSet, ChapterByLessonView
from django.urls import path, include

router = DefaultRouter()
router.register(r"lessons", LessonViewSet, basename="lessons")
router.register(r"chapters", ChapterViewSet, basename="chapters")

urlpatterns = [
    path("", include(router.urls)),
    path('lessons/<int:lesson_id>/chapters/', ChapterByLessonView.as_view(), name='chapters-by-lesson'),
]