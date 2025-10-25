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

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizFullDetailSerializer(quiz, context={'request': request})  # Changed this
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        quiz = self.get_object()
        attempt_id = request.query_params.get('attempt_id')

        attempt = QuizAttempt.objects.filter(id=attempt_id, quiz=quiz, user=request.user).first()
        if not attempt:
            return Response({'detail': 'Attempt not found'}, status=404)

        serializer = QuizResultSerializer(quiz, context={'attempt': attempt})
        return Response(serializer.data)


class QuizAttemptSubmitAPIView(generics.CreateAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSubmitSerializer
    permission_classes = [permissions.IsAuthenticated]