from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    UserListView, 
    UserDetailView, 
    KYCSubmitView,
    KYCStatusView,     
    KYCApproveView      
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),

    path("users/", UserListView.as_view(), name="users-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),

    path("kyc/submit/", KYCSubmitView.as_view(), name="kyc-submit"),
    path("kyc/status/", KYCStatusView.as_view(), name="kyc-status"),          # user checks KYC
    path("kyc/approve/<int:pk>/", KYCApproveView.as_view(), name="kyc-approve"),  # admin approves
]
