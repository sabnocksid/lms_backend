from django.urls import path
from .views import (
    LessonListCreateView,
    LessonRetrieveUpdateDestroyView,
    ChapterListCreateView,
    ChapterRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list-create"),
    path("lessons/<int:pk>/", LessonRetrieveUpdateDestroyView.as_view(), name="lesson-detail"),

    path("lessons/<int:lesson_id>/chapters/", ChapterListCreateView.as_view(), name="chapter-list-create"),
    path("chapters/<int:pk>/", ChapterRetrieveUpdateDestroyView.as_view(), name="chapter-detail"),
]
