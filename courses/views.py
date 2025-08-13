from rest_framework import viewsets, generics, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Category, Course, Chapter, Lesson, UserLessonKey
from .serializers import CategorySerializer, CourseSerializer, ChapterSerializer, LessonSerializer, UserLessonKeySerializer, LessonDetailSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
 

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]



class LessonDetailView(generics.RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserLessonKeyUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLessonKeySerializer 

    def patch(self, request, lesson_id):
        user = request.user
        lesson = get_object_or_404(Lesson, id=lesson_id)
        key_obj, _ = UserLessonKey.objects.get_or_create(user=user, lesson=lesson)

        serializer = self.serializer_class(key_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(partial_decryption_completed=True)
            return Response({"detail": "Partial key updated and completion marked."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)