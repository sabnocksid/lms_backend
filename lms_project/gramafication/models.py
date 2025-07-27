from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson

User = get_user_model()

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    badges = models.ManyToManyField('Badge', blank=True, related_name='students')

    def __str__(self):
        return f"{self.user.username} Profile"

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='badges/', blank=True, null=True)

    def __str__(self):
        return self.name

class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            ('student', 'lesson'),
            ('student', 'course'),
        )

    def __str__(self):
        target = self.lesson or self.course
        return f"{self.student.username} progress on {target}"

class LevelRule(models.Model):
    level = models.PositiveIntegerField(unique=True)
    min_points = models.PositiveIntegerField()

    def __str__(self):
        return f"Level {self.level} (min points: {self.min_points})"
