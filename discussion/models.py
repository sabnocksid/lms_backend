from django.db import models
from django.conf import settings
from courses.models import Course

class DiscussionThread(models.Model):
    course = models.ForeignKey(Course, related_name="threads", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class DiscussionPost(models.Model):
    thread = models.ForeignKey(DiscussionThread, related_name="posts", on_delete=models.CASCADE)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies"
    )

    def __str__(self):
        return f"Post by {self.creator} on {self.thread.title}"
