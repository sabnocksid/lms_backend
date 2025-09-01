from rest_framework import serializers
from .models import Category, Lesson, LessonSection, LessonResource, LessonProgress


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class LessonResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonResource
        fields = "__all__"


class LessonSectionSerializer(serializers.ModelSerializer):
    resources = LessonResourceSerializer(many=True, read_only=True)

    class Meta:
        model = LessonSection
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    sections = LessonSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = "__all__"


class LessonProgressSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    lesson = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LessonProgress
        fields = "__all__"
