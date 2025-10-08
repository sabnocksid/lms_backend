from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings


class LearnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        related_name="learner_profile"
    )
    full_name = models.CharField(max_length=150)
    profile_image = models.ImageField(upload_to='learners/profile_images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)

    points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    rank = models.CharField(max_length=50, default="Beginner")

    def __str__(self):
        return self.full_name or self.user.username

    def add_points(self, points, reason=""):
        from .models import PointTransaction
        PointTransaction.objects.create(learner=self, points=points, reason=reason)

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

    @staticmethod
    def get_leaderboard(top_n=10):
        return LearnerProfile.objects.order_by("-points")[:top_n]

    def get_rank_position(self):
        higher_points = LearnerProfile.objects.filter(points__gt=self.points).count()
        return higher_points + 1


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, help_text="Icon name (e.g., beginner, pro, elite)")
    points_required = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class PointTransaction(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField() 
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.learner.points += self.points
        self.learner.update_rank()
        self.learner.save(update_fields=["points"])

    def __str__(self):
        return f"{self.points} pts - {self.learner.user.username}"


class LearnerBadge(models.Model):
    learner = models.ForeignKey(LearnerProfile, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("learner", "badge")

    def __str__(self):
        return f"{self.learner.user.username} earned {self.badge.name}"
