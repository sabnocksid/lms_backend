from django.urls import path
from .views import QuizListView, QuizDetailView, QuizAttemptCreateView

urlpatterns = [
    path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('attempt/', QuizAttemptCreateView.as_view(), name='quiz-attempt'),
]
 