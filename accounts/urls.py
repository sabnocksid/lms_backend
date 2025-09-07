from django.urls import path
from .views import RegisterView, LoginView, UserListView, UserDetailView, KYCSubmitView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("users/", UserListView.as_view(), name="users-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("kyc/submit/", KYCSubmitView.as_view(), name="kyc-submit"),
]
