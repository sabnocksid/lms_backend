from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    UserListView,
    UserDetailView,
    VerifyEmailView,
    UserRoleViewSet,
)

router = DefaultRouter()
router.register(r'role', UserRoleViewSet, basename='userrole')

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("users/", UserListView.as_view(), name="users-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    
    path("", include(router.urls)),
]
