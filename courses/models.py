from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now)

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses"
    )

    categories = models.ManyToManyField(
        Category,
        related_name="courses",
        blank=True
    )

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    duration = models.DurationField(null=True, blank=True)

    class Meta:
        ordering = ["-date_added"]

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings.exists():
            return 0
        total_points = sum(r.points for r in ratings)
        return round(total_points / ratings.count(), 2)


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="ratings")
    points = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} -> {self.course.name}: {self.points}"
