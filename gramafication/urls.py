from django.urls import path
from .views import (
    LearnerProfileListView, LearnerProfileDetailView,
    TaskListView, TaskCompletionView, TaskCreateView,
    LeaderboardView, LearnerRankView, LearnerProfileUpdateView
)

urlpatterns = [
    # Learner Profiles
    path("learners/", LearnerProfileListView.as_view(), name="learner-list"),
    path("learners/<int:pk>/", LearnerProfileDetailView.as_view(), name="learner-detail"),

    # Tasks
    path("tasks/", TaskListView.as_view(), name="task-list"),
    path("tasks/add/", TaskCreateView.as_view(), name="task-add"),
    path("learners/<int:learner_id>/tasks/<int:task_id>/complete/", TaskCompletionView.as_view(),),

    # Leaderboard
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("learners/<int:learner_id>/rank/", LearnerRankView.as_view(), name="learner-rank"),

    #update learner profile
    path('learner/profile/update/', LearnerProfileUpdateView.as_view(), name='update-learner-profile'),

]
