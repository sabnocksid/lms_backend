from rest_framework import viewsets, generics
from rest_framework.response import Response
from .models import Quiz, QuizAttempt
from .serializers import (
    QuizSerializer, QuizDetailSerializer, QuizUserDetailSerializer
)

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

class QuizDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    lookup_field = 'pk'

class QuizUserDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizUserDetailSerializer
    lookup_field = 'pk'
