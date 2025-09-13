from rest_framework import serializers
from .models import Lesson


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "description",
            "video_file",
            "order",
            "is_published",
            "created_by",
            "date_created",
            "date_updated",
        ]
        read_only_fields = ["created_by", "date_created", "date_updated"]


class LessonDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "course", "order", "is_published"]
