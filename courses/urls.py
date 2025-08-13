from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, ChapterViewSet, LessonViewSet, UserLessonKeyUpdateView, LessonDetailView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'lessons', LessonViewSet)
# router.register(r'watch', LessonDetailView )

urlpatterns = [
    path('', include(router.urls)),
    path('lesson/<int:lesson_id>/partial-key/', UserLessonKeyUpdateView.as_view(), name='lesson-partial-key'),
    path('lesson/playback/<int:lesson_id>/', UserLessonKeyUpdateView.as_view(), name='lesson-playback'),
    path('lessons/<int:pk>/watch/', LessonDetailView.as_view(), name='lesson-detail'),
]
