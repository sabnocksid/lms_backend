from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Lesson
from .serializers import LessonSerializer
from .utils.upload_minio import upload_file_to_minio

class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('-created_at')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def handle_file_upload(self, file_field, folder):

        files = self.request.FILES.getlist(file_field)
        if not files:
            return None

        urls = []
        for f in files:
            url = upload_file_to_minio(f, f"{folder}/{f.name}")
            if url:
                urls.append(url)

        return urls[0] if len(urls) == 1 else urls

    def perform_create(self, serializer):
        data = self.request.data.copy()

        video_url = self.handle_file_upload("video", "videos")
        if video_url:
            data["video"] = video_url

        material_url = self.handle_file_upload("material", "materials")
        if material_url:
            data["material"] = material_url

        serializer.save(**data)

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def handle_file_upload(self, file_field, folder):

        files = self.request.FILES.getlist(file_field)
        if not files:
            return None

        urls = []
        for f in files:
            url = upload_file_to_minio(f, f"{folder}/{f.name}")
            if url:
                urls.append(url)

        return urls[0] if len(urls) == 1 else urls

    def perform_update(self, serializer):
        data = self.request.data.copy()

        video_url = self.handle_file_upload("video", "videos")
        if video_url:
            data["video"] = video_url

        material_url = self.handle_file_upload("material", "materials")
        if material_url:
            data["material"] = material_url

        serializer.save(**data)
