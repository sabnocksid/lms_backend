from rest_framework import serializers
from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    videos = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    materials = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description',  'videos', 'materials', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        videos = validated_data.pop('videos', [])
        materials = validated_data.pop('materials', [])
        lesson = Lesson.objects.create(**validated_data)
        if videos:
            lesson.video.save(videos[0].name, videos[0])
        if materials:
            lesson.material.save(materials[0].name, materials[0])
        return lesson

