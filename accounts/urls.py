from django.urls import path
from .views import RegisterView, KYCSubmitView, KYCApproveView, KYCDownloadView, LoginView, PendingKYCUserListView, UserListView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path("register/", RegisterView.as_view(), name="register"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("kyc/submit/", KYCSubmitView.as_view(), name="kyc-submit"),
    path("kyc/approve/<int:pk>/", KYCApproveView.as_view(), name="kyc-approve"),
    path("kyc/download/<int:pk>/", KYCDownloadView.as_view(), name="kyc-download"),
    path('kyc/pending-users/', PendingKYCUserListView.as_view(), name='kyc-pending-users'),
]