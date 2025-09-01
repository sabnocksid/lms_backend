from rest_framework import serializers
from .models import Category, Lesson, LessonResource, LessonProgress, LessonReview
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class LessonResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonResource
        fields = "__all__"


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = "__all__"
        read_only_fields = ["user"]  


class LessonReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonReview
        fields = "__all__"
        read_only_fields = ["user"]
