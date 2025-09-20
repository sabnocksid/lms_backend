from rest_framework import serializers
from .models import Lesson, Chapter
from .utils.upload_minio import upload_file_to_minio, get_public_url

class LessonSerializer(serializers.ModelSerializer):
    thumbnail_file = serializers.FileField(write_only=True, required=False)
    thumbnail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'thumbnail', 'thumbnail_file', 'created_at']
        read_only_fields = ['id', 'thumbnail', 'created_at']

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            return get_public_url(obj.thumbnail)
        return None

    def create(self, validated_data):
        file_obj = validated_data.pop('thumbnail_file', None)
        lesson = Lesson.objects.create(**validated_data)
        if file_obj:
            key = upload_file_to_minio(file_obj, f"lessons/thumbnails/{file_obj.name}")
            lesson.thumbnail = key
            lesson.save()
        return lesson

    def update(self, instance, validated_data):
        file_obj = validated_data.pop('thumbnail_file', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if file_obj:
            key = upload_file_to_minio(file_obj, f"lessons/thumbnails/{file_obj.name}")
            instance.thumbnail = key
        instance.save()
        return instance


class ChapterSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(write_only=True, required=False)
    material_file = serializers.FileField(write_only=True, required=False)
    video = serializers.SerializerMethodField(read_only=True)
    material = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'lesson', 'title', 'video', 'material', 'video_file', 'material_file', 'created_at']
        read_only_fields = ['id', 'video', 'material', 'created_at']

    def get_video(self, obj):
        if obj.video:
            return get_public_url(obj.video)
        return None

    def get_material(self, obj):
        if obj.material:
            return get_public_url(obj.material)
        return None

    def create(self, validated_data):
        video_file = validated_data.pop('video_file', None)
        material_file = validated_data.pop('material_file', None)
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
        video_file = validated_data.pop('video_file', None)
        material_file = validated_data.pop('material_file', None)

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
