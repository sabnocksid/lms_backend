from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course
from quizes.models import Quiz, QuizAttempt
from lessons.models import Chapter, ChapterProgress


class LearnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
         related_name='profile'
    )
    full_name = models.CharField(max_length=150)
    profile_image = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)

    points = models.IntegerField(default=0)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    rank = models.CharField(max_length=50, default="Beginner")

    def __str__(self):
        return self.full_name or self.user.username

    def update_rank(self):
        prev_rank = self.rank
        if self.points >= 1000:
            self.rank = "Elite"
        elif self.points >= 500:
            self.rank = "Pro"
        elif self.points >= 200:
            self.rank = "Intermediate"
        else:
            self.rank = "Beginner"

        if self.rank != prev_rank:
            self.save(update_fields=["rank"])
            self.assign_badge_for_rank()

    def assign_badge_for_rank(self):
        badge, _ = Badge.objects.get_or_create(
            name=self.rank,
            defaults={
                "description": f"Badge for achieving {self.rank} rank",
                "icon": self.rank.lower(),
                "points_required": 0
            }
        )
        LearnerBadge.objects.get_or_create(learner=self, badge=badge)

    def add_points(self, points, reason=""):
        PointTransaction.objects.create(learner=self, points=points, reason=reason)

    @staticmethod
    def get_leaderboard(top_n=10):
        return LearnerProfile.objects.order_by("-points")[:top_n]

    def get_rank_position(self):
        higher_points = LearnerProfile.objects.filter(points__gt=self.points).count()
        return higher_points + 1


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100)
    points_required = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class LearnerBadge(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("learner", "badge")

    def __str__(self):
        return f"{self.learner.user.username} earned {self.badge.name}"



class PointTransaction(models.Model):
    learner = models.ForeignKey("LearnerProfile", on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.learner.points += self.points
            self.learner.update_rank()
            self.learner.save(update_fields=["points", "rank"])

    def __str__(self):
        sign = "+" if self.points >= 0 else "-"
        return f"{sign}{abs(self.points)} pts - {self.learner.user.username}"
    

class Enrollment(models.Model):
    learner = models.ForeignKey(
        LearnerProfile,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments" 
    )
    date_enrolled = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True) 
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("learner", "course")

    def __str__(self):
        return f"{self.learner.full_name} enrolled in {self.course.name}"


class CourseGamification(models.Model):
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="gamification"
    )
    points_earned = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.enrollment.learner.full_name} - {self.enrollment.course.name}"

    @property
    def total_chapters(self):
        return Chapter.objects.filter(lesson__course=self.enrollment.course).count()

    @property
    def completed_chapters(self):
        return ChapterProgress.objects.filter(
            user=self.enrollment.learner.user, 
            chapter__lesson__course=self.enrollment.course,
            completed=True
        ).count()

    @property
    def total_quizzes(self):
        return Quiz.objects.filter(course=self.enrollment.course).count()

    @property
    def attempted_quizzes(self):
        return QuizAttempt.objects.filter(
            user=self.enrollment.learner.user,
            quiz__course=self.enrollment.course
        ).count()

    @property
    def course_completed(self):
        chapter_done = self.completed_chapters >= self.total_chapters if self.total_chapters else True
        quiz_done = self.attempted_quizzes >= self.total_quizzes if self.total_quizzes else True
        return chapter_done and quiz_done

from courses.models import Course

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
        return f"{self.actor} {self.verb} {self.target_course if self.target_course else ''}"
