from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, ChapterViewSet, LessonViewSet, UserLessonKeyUpdateView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'lessons', LessonViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('lesson/<int:lesson_id>/partial-key/', UserLessonKeyUpdateView.as_view(), name='lesson-partial-key'),
]
