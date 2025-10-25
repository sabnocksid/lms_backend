from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quiz, QuizAttempt
from .serializers import QuizSerializer, QuizDetailSerializer, QuizResultSerializer, QuizAttemptSerializer

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizDetailSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_attempt(self, request, pk=None):
        quiz = self.get_object()
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
        serializer = QuizAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(attempt=attempt)
        return Response({"attempt_id": attempt.id})

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        quiz = self.get_object()
        attempt_id = request.query_params.get('attempt_id')
        attempt = QuizAttempt.objects.get(id=attempt_id, quiz=quiz, user=request.user)
        serializer = QuizResultSerializer(quiz, context={'attempt': attempt})
        return Response(serializer.data)
