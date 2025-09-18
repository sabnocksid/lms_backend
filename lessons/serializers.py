from rest_framework import serializers
from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    # For input
    videos = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    materials = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    # For output
    video_url = serializers.SerializerMethodField()
    material_url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description',
            'video', 'material',  # original single-file fields
            'video_url', 'material_url',  # for response
            'videos', 'materials',  # only for input
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'video_url', 'material_url']

    def create(self, validated_data):
        videos = validated_data.pop('videos', [])
        materials = validated_data.pop('materials', [])
        lesson = Lesson.objects.create(**validated_data)
        if videos:
            lesson.video.save(videos[0].name, videos[0])
        if materials:
            lesson.material.save(materials[0].name, materials[0])
        return lesson

    def get_video_url(self, obj):
        if obj.video:
            return obj.video.url
        return None

    def get_material_url(self, obj):
        if obj.material:
            return obj.material.url
        return None
