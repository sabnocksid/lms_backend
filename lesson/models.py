from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course
import os
from .utils import encrypt_video_file

User = get_user_model()


def lesson_video_upload_path(instance, filename):
    """Dynamic path: videos/course_<id>/lesson_<id>/user_<id>/filename"""
    user_id = instance.created_by.id if instance.created_by else "anonymous"
    lesson_id = instance.id if instance.id else "temp"
    return f"videos/course_{instance.course.id}/lesson_{lesson_id}/user_{user_id}/{filename}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to=lesson_video_upload_path, null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("course", "order")

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.video_file and "lesson_temp" in self.video_file.name:
            old_path = self.video_file.path
            new_dir = os.path.join(
                os.path.dirname(old_path).replace("lesson_temp", f"lesson_{self.id}")
            )
            os.makedirs(new_dir, exist_ok=True)
            new_path = os.path.join(new_dir, os.path.basename(old_path))
            os.rename(old_path, new_path)
            self.video_file.name = os.path.relpath(new_path, start=os.path.dirname(old_path).split("media")[0]+"media")
            super().save(update_fields=["video_file"])

        if self.video_file and self.created_by:
            encrypt_video_file(self.video_file.path, self.created_by)
