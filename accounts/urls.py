from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    UserListView,
    UserDetailView,
    VerifyEmailView,
    UserRoleViewSet,
    AdminUserCreateView,
    UserUpdateAPIView,
    logout_view
)

router = DefaultRouter()
router.register(r'role', UserRoleViewSet, basename='userrole')

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("users/", UserListView.as_view(), name="users-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("user/update/<int:user_id>/", UserUpdateAPIView.as_view(), name="user-update"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path('admin/create-user/', AdminUserCreateView.as_view(), name='admin-create-user'),
    path("logout/", logout_view, name="logout"),

    
    path("", include(router.urls)),
]
