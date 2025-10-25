from django.urls import path
from .views import (
    LearnerProfileListView,
    LearnerProfileDetailView,
    LearnerProfileUpdateView,
    LeaderboardView,
    CourseGamificationView,
)

urlpatterns = [
    path("learners/", LearnerProfileListView.as_view(), name="learner-profile-list"),
    path("learners/me/", LearnerProfileDetailView.as_view(), name="learner-profile-detail"),
    path("learners/me/update/", LearnerProfileUpdateView.as_view(), name="learner-profile-update"),

    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),

    path("course/<int:course_id>/progress/", CourseGamificationView.as_view(), name="course-gamification-progress"),
]
