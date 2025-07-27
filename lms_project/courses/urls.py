from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CourseViewSet, LessonViewSet, VideoViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'videos', VideoViewSet)
router.register(r'enrollments', EnrollmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
