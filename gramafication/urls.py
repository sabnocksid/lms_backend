from django.urls import path
from .views import (
    LearnerProfileListView,
    LearnerProfileDetailView,
    LearnerProfileUpdateView,
    LeaderboardView,
    FullLeaderboardView,
    CourseGamificationView,
    DashboardView,
    EnrollCourseView, 
    MyEnrollmentsView,
    PointTransactionListView
)

urlpatterns = [
    path("learners/me/update/", LearnerProfileUpdateView.as_view(), name="learner-profile-update"),

    path("learners/", LearnerProfileListView.as_view(), name="learner-profile-list"),
    path('engagements/', PointTransactionListView.as_view(), name='engagements'),
    path("learners/me/", LearnerProfileDetailView.as_view(), name="learner-profile-detail"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("leaderboard/", FullLeaderboardView.as_view(), name="leaderboard"),
    path("enroll/<int:course_id>", EnrollCourseView.as_view(), name="enroll-course"),
    path("my-enrollments/", MyEnrollmentsView.as_view(), name="user-enrollments"),

    path("course/<int:course_id>/progress/", CourseGamificationView.as_view(), name="course-gamification-progress"),
]
