from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import StudentProfileViewSet, BadgeViewSet, StudentProgressViewSet, LevelRuleViewSet

router = DefaultRouter()
router.register(r'profiles', StudentProfileViewSet)
router.register(r'badges', BadgeViewSet)
router.register(r'progress', StudentProgressViewSet)
router.register(r'levels', LevelRuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
