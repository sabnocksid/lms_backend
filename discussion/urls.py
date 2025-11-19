from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscussionThreadViewSet, DiscussionPostViewSet

router = DefaultRouter()
router.register(r"threads", DiscussionThreadViewSet, basename="threads")
router.register(r"posts", DiscussionPostViewSet, basename="posts")

urlpatterns = [
    path("", include(router.urls)),
]
