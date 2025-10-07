from django.db import models
from django.conf import settings
from django.utils import timezone


class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Chapter(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="chapters", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    video = models.URLField(max_length=500, blank=True, null=True)
    material = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class ChapterProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chapter_progress"
    )
    chapter = models.ForeignKey(
        "Chapter", on_delete=models.CASCADE, related_name="user_progress"
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "chapter")
        ordering = ["chapter"]

    def __str__(self):
        return f"{self.user.email} - {self.chapter.title} ({'Done' if self.completed else 'In Progress'})"

    def mark_completed(self):
        self.completed = True
        self.completed_at = timezone.now()
        self.save()