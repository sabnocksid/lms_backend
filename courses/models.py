import os
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Chapter(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('document', 'Document'),
        ('quiz', 'Quiz'),
    ]

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)

    video_file = models.FileField(
        upload_to="lesson_videos/originals/",
        blank=True,
        null=True
    )
    document = models.FileField(
        upload_to='lesson_documents/originals/',
        blank=True,
        null=True
    )
    content = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.chapter.title} - {self.title}"

    def generate_key(self):
        return os.urandom(32)


class UserLessonKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_keys')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_keys')
    encrypted_key = models.BinaryField() 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"Key for {self.user} - Lesson {self.lesson.id}"

    def get_raw_key(self):
        return self.encrypted_key
