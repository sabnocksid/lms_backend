from django.urls import path
from .views import (
    LearnerProfileListView,
    LearnerProfileDetailView,
    LearnerProfileUpdateView,
    LeaderboardView,
    CourseGamificationView,
    DashboardView
)

urlpatterns = [
    path("learners/me/update/", LearnerProfileUpdateView.as_view(), name="learner-profile-update"),

    path("learners/", LearnerProfileListView.as_view(), name="learner-profile-list"),
    path("learners/me/", LearnerProfileDetailView.as_view(), name="learner-profile-detail"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),

    path("course/<int:course_id>/progress/", CourseGamificationView.as_view(), name="course-gamification-progress"),
]
