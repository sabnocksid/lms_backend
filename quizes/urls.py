from django.urls import path
from .views import (
    CreateMCQQuestion, CreateTextQuestion, CreateTFQuestion,
    QuizQuestionsList, SubmitQuizAttempt
)

urlpatterns = [
    # Create questions
    path('questions/mcq/', CreateMCQQuestion.as_view(), name='create-mcq'),
    path('questions/text/', CreateTextQuestion.as_view(), name='create-text'),
    path('questions/tf/', CreateTFQuestion.as_view(), name='create-tf'),

    # Get questions (filtered by query param)
    path('quiz/<int:quiz_id>/questions/', QuizQuestionsList.as_view(), name='quiz-questions'),

    # Submit attempt
    path('quiz/<int:quiz_id>/attempt/', SubmitQuizAttempt.as_view(), name='submit-quiz'),
]
