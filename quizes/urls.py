from django.urls import path
from . import views

urlpatterns = [
    path('quizzes/', views.ListQuizView.as_view(), name='list-quizzes'),      
    path('quizzes/create/', views.CreateQuizView.as_view(), name='create-quiz'),  

    path('quizzes/<int:quiz_id>/mcq/', views.ListMCQQuestions.as_view(), name='list-mcq-questions'), 
    path('quizzes/mcq/create/', views.CreateMCQQuestion.as_view(), name='create-mcq-question'),    

    path('quizzes/<int:quiz_id>/text/', views.ListTextQuestions.as_view(), name='list-text-questions'),
    path('quizzes/text/create/', views.CreateTextQuestion.as_view(), name='create-text-question'),     

    path('quizzes/<int:quiz_id>/tf/', views.ListTFQuestions.as_view(), name='list-tf-questions'),      
    path('quizzes/tf/create/', views.CreateTFQuestion.as_view(), name='create-tf-question'),         
    path('quizzes/<int:pk>/attempt/', views.SubmitQuizAttempt.as_view(), name='submit-quiz-attempt'),    
    path('quizzes/<int:quiz_id>/result/', views.QuizResultView.as_view(), name='quiz-result'),
]
