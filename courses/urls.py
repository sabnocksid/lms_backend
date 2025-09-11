from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, CourseRatingViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'ratings', CourseRatingViewSet, basename='ratings')

urlpatterns = [
    path('', include(router.urls)),
]