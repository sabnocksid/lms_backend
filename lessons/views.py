# views.py
from rest_framework import generics
from .models import Lesson
from .serializers import LessonSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .utils.upload_minio import upload_file_to_minio

class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        data = self.request.data.copy()

        if "video" in self.request.FILES:
            video_file = self.request.FILES["video"]
            video_url = upload_file_to_minio(video_file, f"videos/{video_file.name}")
            if video_url:
                data["video"] = video_url

        if "material" in self.request.FILES:
            material_file = self.request.FILES["material"]
            material_url = upload_file_to_minio(material_file, f"materials/{material_file.name}")
            if material_url:
                data["material"] = material_url

        serializer.save(**data)

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        data = self.request.data.copy()

        if "video" in self.request.FILES:
            video_file = self.request.FILES["video"]
            video_url = upload_file_to_minio(video_file, f"videos/{video_file.name}")
            if video_url:
                data["video"] = video_url

        if "material" in self.request.FILES:
            material_file = self.request.FILES["material"]
            material_url = upload_file_to_minio(material_file, f"materials/{material_file.name}")
            if material_url:
                data["material"] = material_url

        serializer.save(**data)
