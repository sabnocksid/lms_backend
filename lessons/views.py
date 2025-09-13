from rest_framework import generics
from .models import Lesson
from .serializers import LessonSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]  

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]
