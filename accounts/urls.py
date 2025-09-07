from django.urls import path
from .views import (
    RegisterView, LoginView,
    UserListView, UserRetrieveView, UserUpdateView, UserPartialUpdateView, UserDeleteView,
    KYCSubmitView, PendingKYCUserListView, KYCApproveView, KYCDownloadView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserRetrieveView.as_view(), name='user-retrieve'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/partial/', UserPartialUpdateView.as_view(), name='user-partial-update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),

    path('kyc/submit/', KYCSubmitView.as_view(), name='kyc-submit'),
    path('kyc/pending/', PendingKYCUserListView.as_view(), name='kyc-pending'),
    path('kyc/approve/<int:pk>/', KYCApproveView.as_view(), name='kyc-approve'),
    path('kyc/download/<int:pk>/', KYCDownloadView.as_view(), name='kyc-download'),
]
