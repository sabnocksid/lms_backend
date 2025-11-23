from django.conf import settings
from django.db import models

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    verb = models.CharField(max_length=255)

    target_course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.actor} {self.verb} {self.target_course or ''}"
