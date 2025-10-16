from rest_framework import generics
from .models import Quiz, QuizAttempt
from .serializers import QuizSerializer, QuizAttemptSerializer

class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

class QuizDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

class QuizAttemptCreateView(generics.CreateAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer
