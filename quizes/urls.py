from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizCreateAPIView, QuizAttemptView

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path('quizzes/create/', QuizCreateAPIView.as_view(), name='quiz-create'),
    path('attempts/', QuizAttemptView.as_view(), name='quiz-attempt'),
    path('', include(router.urls)),
]
