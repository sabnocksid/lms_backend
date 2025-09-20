from rest_framework import serializers
from .models import Lesson, Chapter


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'video', 'material', 'created_at']
        read_only_fields = ['id', 'created_at']


class LessonSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'thumbnail', 'chapters', 'created_at']
        read_only_fields = ['id', 'created_at']
