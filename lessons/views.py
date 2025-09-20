from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Lesson, Chapter
from .serializers import LessonSerializer, ChapterSerializer
from .utils.upload_minio import upload_file_to_minio


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        thumbnail_file = self.request.FILES.get("thumbnail")
        if thumbnail_file:
            url = upload_file_to_minio(thumbnail_file, f"lessons/thumbnails/{thumbnail_file.name}")
            serializer.save(thumbnail=url)
        else:
            serializer.save()


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        thumbnail_file = self.request.FILES.get("thumbnail")
        if thumbnail_file:
            url = upload_file_to_minio(thumbnail_file, f"lessons/thumbnails/{thumbnail_file.name}")
            serializer.save(thumbnail=url)
        else:
            serializer.save()


class ChapterListCreateView(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Chapter.objects.filter(lesson_id=self.kwargs["lesson_id"]).order_by('-created_at')

    def perform_create(self, serializer):
        video_file = self.request.FILES.get("video")
        material_file = self.request.FILES.get("material")
        data = {"lesson_id": self.kwargs["lesson_id"]}

        if video_file:
            data["video"] = upload_file_to_minio(video_file, f"chapters/videos/{video_file.name}")
        if material_file:
            data["material"] = upload_file_to_minio(material_file, f"chapters/materials/{material_file.name}")

        serializer.save(**data)


class ChapterRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        video_file = self.request.FILES.get("video")
        material_file = self.request.FILES.get("material")
        data = {}

        if video_file:
            data["video"] = upload_file_to_minio(video_file, f"chapters/videos/{video_file.name}")
        if material_file:
            data["material"] = upload_file_to_minio(material_file, f"chapters/materials/{material_file.name}")

        serializer.save(**data)
