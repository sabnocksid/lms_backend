from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quiz, QuizAttempt
from .serializers import (
    QuizCreateSerializer,
    QuizFullDetailSerializer,  
    QuizAttemptSubmitSerializer,
    QuizResultSerializer,
    UserAnswerSerializer
)


class QuizCreateAPIView(generics.CreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizFullDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='quiz-detail')  
    def quiz_detail(self, request, pk=None):  
        quiz = self.get_object()
        serializer = QuizFullDetailSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        attempts = QuizAttempt.objects.filter(quiz=quiz, user=user).order_by('-completed_at')
        if not attempts.exists():
            return Response({'detail': 'No attempts found'}, status=404)

        results = [
            QuizResultSerializer(quiz, context={'attempt': attempt}).data
            for attempt in attempts
        ]

        return Response(results)


class QuizAttemptSubmitAPIView(generics.CreateAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSubmitSerializer
    permission_classes = [permissions.IsAuthenticated]