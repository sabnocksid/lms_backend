from rest_framework import serializers
from .models import Category, Course


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


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
            "description",
            "thumbnail",
            "rating",
            "date_added",
            "instructor_name",
            "category",
            "category_id",
            "price",
            "is_published",
            "duration",
        ]
