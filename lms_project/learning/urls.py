from django.urls import path
from .views import stream_encrypted_video

urlpatterns = [
    path('stream-video/<str:filename>/', stream_encrypted_video, name='stream-encrypted-video'),
]
