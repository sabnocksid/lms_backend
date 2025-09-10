from rest_framework import serializers
from .models import Course, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

class CoursePreviewSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "rating",
            "instructor_name",
            "category",
        ]
        read_only_fields = fields

class CourseDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "thumbnail",
            "rating",
            "date_added",
            "instructor_name",
            "category",
            "price",
            "is_published",
            "duration",
        ]
