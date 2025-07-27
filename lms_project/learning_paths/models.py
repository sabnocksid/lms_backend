from django.db import models
from courses.models import Course

class LearningPath(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    courses = models.ManyToManyField(Course, through='LearningPathCourse', related_name='learning_paths')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class LearningPathCourse(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('learning_path', 'course')
        ordering = ['order']

    def __str__(self):
        return f"{self.learning_path.title} - {self.order}: {self.course.title}"
