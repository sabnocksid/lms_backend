from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import LearningPathViewSet

router = DefaultRouter()
router.register(r'learning-paths', LearningPathViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
