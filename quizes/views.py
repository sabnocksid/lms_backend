from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Quiz, Question
from .serializers import (
    MCQQuestionSerializer, TextQuestionSerializer, TFQuestionSerializer,
    QuizSerializer, QuizAttemptSerializer, QuizCreateSerializer, QuizSerializer
)


class CreateQuizView(generics.CreateAPIView):
    serializer_class = QuizCreateSerializer
    permission_classes = [IsAuthenticated]

class ListQuizView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q_type = self.request.query_params.get('type')
        qs = Quiz.objects.all()
        if q_type:
            qs = qs.filter(questions__question_type=q_type).distinct()
        return qs

# Create questions by type
class CreateMCQQuestion(generics.CreateAPIView):
    serializer_class = MCQQuestionSerializer
    permission_classes = [IsAuthenticated]

class CreateTextQuestion(generics.CreateAPIView):
    serializer_class = TextQuestionSerializer
    permission_classes = [IsAuthenticated]

class CreateTFQuestion(generics.CreateAPIView):
    serializer_class = TFQuestionSerializer
    permission_classes = [IsAuthenticated]

# GET questions with filter
class QuizQuestionsList(generics.ListAPIView):
    serializer_class = MCQQuestionSerializer 
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        q_type = self.request.query_params.get('type')
        if q_type == 'MCQ':
            return MCQQuestionSerializer
        elif q_type == 'TEXT':
            return TextQuestionSerializer
        elif q_type == 'TF':
            return TFQuestionSerializer
        return MCQQuestionSerializer  

    def get_queryset(self):
        quiz_id = self.kwargs['quiz_id']
        q_type = self.request.query_params.get('type')
        qs = Question.objects.filter(quiz_id=quiz_id)
        if q_type:
            qs = qs.filter(question_type=q_type)
        return qs

# Submit quiz attempt
class SubmitQuizAttempt(generics.CreateAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        quiz_id = self.kwargs.get("pk") or self.kwargs.get("id") 
        serializer.save(user=self.request.user, quiz_id=quiz_id)
