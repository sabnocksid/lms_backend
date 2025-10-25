from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, QuizDetailView, QuizUserDetailView

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')

urlpatterns = [
    path('', include(router.urls)),
    path('quizzes/<int:pk>/detail/', QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:pk>/user-detail/', QuizUserDetailView.as_view(), name='quiz-user-detail'),
]
