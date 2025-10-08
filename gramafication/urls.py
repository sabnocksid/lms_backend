from django.urls import path
from .views import (
    LearnerProfileListView,
    LearnerProfileDetailView,
    LeaderboardView,
    LearnerRankView,
    AddPointsView,
)

urlpatterns = [
    path("learners/", LearnerProfileListView.as_view(), name="learner-list"),
    path("learners/<int:pk>/", LearnerProfileDetailView.as_view(), name="learner-detail"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("learners/<int:learner_id>/rank/", LearnerRankView.as_view(), name="learner-rank"),
    path("learners/<int:learner_id>/add-points/", AddPointsView.as_view(), name="add-points"),
]
