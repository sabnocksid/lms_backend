from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="actions")
    verb = models.CharField(max_length=255)
    target_course = models.ForeignKey("courses.Course", null=True, blank=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.verb} -> {self.recipient}"
