from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Quiz, Question, QuizAttempt
from .serializers import (
    MCQQuestionSerializer, TextQuestionSerializer, TFQuestionSerializer,
    QuizSerializer, QuizCreateSerializer, QuizAttemptSerializer
)

class CreateQuizView(generics.CreateAPIView):
    serializer_class = QuizCreateSerializer
    permission_classes = [IsAuthenticated]

class ListQuizView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.all()

class ListMCQQuestions(generics.ListAPIView):
    serializer_class = MCQQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        return Question.objects.filter(quiz_id=quiz_id, question_type='MCQ')

class CreateMCQQuestion(generics.CreateAPIView):
    serializer_class = MCQQuestionSerializer
    permission_classes = [IsAuthenticated]

class ListTextQuestions(generics.ListAPIView):
    serializer_class = TextQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        return Question.objects.filter(quiz_id=quiz_id, question_type='TEXT')

class CreateTextQuestion(generics.CreateAPIView):
    serializer_class = TextQuestionSerializer
    permission_classes = [IsAuthenticated]

class ListTFQuestions(generics.ListAPIView):
    serializer_class = TFQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        return Question.objects.filter(quiz_id=quiz_id, question_type='TF')

class CreateTFQuestion(generics.CreateAPIView):
    serializer_class = TFQuestionSerializer
    permission_classes = [IsAuthenticated]

class SubmitQuizAttempt(generics.CreateAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        quiz_id = self.kwargs.get("pk")
        quiz = Quiz.objects.get(id=quiz_id)
        user = self.request.user
        attempt, created = QuizAttempt.objects.get_or_create(user=user, quiz=quiz)
        serializer.save(attempt=attempt)
