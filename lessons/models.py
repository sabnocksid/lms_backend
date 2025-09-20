from django.db import models

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
