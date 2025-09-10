from rest_framework import serializers
from .models import Course, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]

class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "rating",
            "date_added",
            "instructor_name",
            "category",
        ]

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
