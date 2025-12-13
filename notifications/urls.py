from django.urls import path
from . import views

urlpatterns = [
    path("notifications/<int:notification_id>/", views.delete_notification, name="delete_notification"),
]
