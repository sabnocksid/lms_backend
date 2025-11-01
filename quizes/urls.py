from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizCreateAPIView, QuizAttemptView, QuizUpdateAPIView, QuizDeleteAPIView

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path('quizzes/create/', QuizCreateAPIView.as_view(), name='quiz-create'),
    path("quizzes/update/<int:id>/", QuizUpdateAPIView.as_view(), name="quiz-update"),
    path("quizzes/<int:id>/delete/", QuizDeleteAPIView.as_view(), name="quiz-delete"),
    path('<int:quiz_id>/attempts/', QuizAttemptView.as_view(), name='quiz-attempt'),
    path('', include(router.urls)),
]
