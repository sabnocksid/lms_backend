from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Lesson, Chapter
from .serializers import LessonSerializer, ChapterSerializer


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]


class ChapterListCreateView(generics.ListCreateAPIView):
    queryset = Chapter.objects.all().order_by('-created_at')
    serializer_class = ChapterSerializer
    parser_classes = [MultiPartParser, FormParser]

class ChapterRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    parser_classes = [MultiPartParser, FormParser]
