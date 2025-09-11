from rest_framework import serializers
from .models import Course, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]  


class CoursePreviewSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)  
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "rating",
            "instructor_name",
            "categories",
        ]
        read_only_fields = fields 


class CourseDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)  
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
            "categories",
            "price",
            "is_published",
            "duration",
        ]


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source="categories"  
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "thumbnail",
            "rating",
            "category_ids",   
            "price",
            "is_published",
            "duration",
        ]
