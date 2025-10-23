from rest_framework import serializers
from .models import Lesson, Chapter,  ChapterProgress
from courses.models import Course

from .utils.upload_minio import (
    upload_file_to_minio,
    get_public_url,
    get_presigned_url,
)

class ChapterSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(write_only=True, required=False)
    material_file = serializers.FileField(write_only=True, required=False)
    video = serializers.SerializerMethodField(read_only=True)
    material = serializers.SerializerMethodField(read_only=True)
    progress = serializers.SerializerMethodField(read_only=True)  

    class Meta:
        model = Chapter
        fields = [
            "id",
            "lesson",
            "title",
            "video",
            "material",
            "progress",  
            "video_file",
            "material_file",
            "created_at",
        ]
        read_only_fields = ["id", "video", "material", "progress", "created_at"]

    def get_video(self, obj):
        if obj.video:
            request = self.context.get("request")
            return get_presigned_url(obj.video, request=request)
        return None

    def get_material(self, obj):
        if obj.material:
            request = self.context.get("request")
            return get_presigned_url(obj.material, request=request)
        return None

    def get_progress(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            progress, _ = ChapterProgress.objects.get_or_create(user=request.user, chapter=obj)
            return {
                "completed": progress.completed,
                "completed_at": progress.completed_at
            }
        return {"completed": False, "completed_at": None}

    def create(self, validated_data):
        video_file = validated_data.pop("video_file", None)
        material_file = validated_data.pop("material_file", None)
        chapter = Chapter.objects.create(**validated_data)

        if video_file:
            key = upload_file_to_minio(video_file, f"chapters/videos/{video_file.name}")
            chapter.video = key
        if material_file:
            key = upload_file_to_minio(material_file, f"chapters/materials/{material_file.name}")
            chapter.material = key

        chapter.save()
        return chapter

    def update(self, instance, validated_data):
        video_file = validated_data.pop("video_file", None)
        material_file = validated_data.pop("material_file", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if video_file:
            key = upload_file_to_minio(video_file, f"chapters/videos/{video_file.name}")
            instance.video = key
        if material_file:
            key = upload_file_to_minio(material_file, f"chapters/materials/{material_file.name}")
            instance.material = key

        instance.save()
        return instance
    

class LessonWithChapterCountSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    chapter_count = serializers.SerializerMethodField()  

    class Meta:
        model = Lesson
        fields = [
            "id", "course", "title", "description", "thumbnail", 
            "created_at", "chapter_count"
        ]
        read_only_fields = ["id", "created_at", "chapter_count"]

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(obj.thumbnail, request=request)
        return None

    def get_chapter_count(self, obj):
        return obj.chapters.count()  



class LessonDetailSerializer(serializers.ModelSerializer):
    thumbnail_file = serializers.FileField(write_only=True, required=False)
    thumbnail = serializers.SerializerMethodField(read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    chapters = ChapterSerializer(many=True, read_only=True)  # Include chapters

    class Meta:
        model = Lesson
        fields = [
            "id", "course", "title", "description", "thumbnail", 
            "thumbnail_file", "created_at", "chapters"
        ]
        read_only_fields = ["id", "thumbnail", "created_at", "chapters"]

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(obj.thumbnail, request=request)
        return None

    def create(self, validated_data):
        file_obj = validated_data.pop("thumbnail_file", None)
        lesson = Lesson.objects.create(**validated_data)
        if file_obj:
            key = upload_file_to_minio(file_obj, f"lessons/thumbnails/{file_obj.name}")
            lesson.thumbnail = key
            lesson.save()
        return lesson

    def update(self, instance, validated_data):
        file_obj = validated_data.pop("thumbnail_file", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if file_obj:
            key = upload_file_to_minio(file_obj, f"lessons/thumbnails/{file_obj.name}")
            instance.thumbnail = key
        instance.save()
        return instance




    
class ChapterProgressSerializer(serializers.ModelSerializer):
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)

    class Meta:
        model = ChapterProgress
        fields = ["id", "chapter", "chapter_title", "completed", "completed_at"]
        read_only_fields = ["completed_at"]


class ChapterProgressSerializer(serializers.ModelSerializer):
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)
    lesson_id = serializers.IntegerField(source="chapter.lesson.id", read_only=True)
    lesson_title = serializers.CharField(source="chapter.lesson.title", read_only=True)

    class Meta:
        model = ChapterProgress
        fields = [
            "id",
            "chapter",
            "chapter_title",
            "lesson_id",
            "lesson_title",
            "completed",
            "completed_at",
        ]
        read_only_fields = ["completed_at", "chapter_title", "lesson_id", "lesson_title"]