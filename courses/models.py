from django.db import models
from django.conf import settings 
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lesson(models.Model):
    category = models.ForeignKey(
        Category, related_name="lessons", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    content = models.TextField(help_text="Markdown or HTML content")
    video_url = models.URLField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name="lessons",
        on_delete=models.SET_NULL,
        null=True
    )
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class LessonResource(models.Model):
    lesson = models.ForeignKey(
        Lesson, related_name="resources", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="lesson_resources/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        related_name="lesson_progress",
        on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(Lesson, related_name="progress", on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user} - {self.lesson.title} ({self.progress_percent}%)"


class LessonReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        related_name="lesson_reviews",
        on_delete=models.CASCADE
    )
    lesson = models.ForeignKey(Lesson, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0)  
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "lesson")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.lesson.title} ({self.rating})"
