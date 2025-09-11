from rest_framework import serializers
from .models import Course, Category, Rating


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]  


class CoursePreviewSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)  
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)  
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "average_rating", 
            "instructor_name",
            "categories",
            "date_added"
        ]
        read_only_fields = fields

class CourseDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, source="average_rating", read_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "thumbnail",
            "date_added",
            "instructor_name",
            "categories",
            "price",
            "is_published",
            "duration",
            "average_rating",
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
            "instructor",
            "description",
            "thumbnail",
            "category_ids",   
            "price",
            "is_published",
            "duration",
        ]



class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "points", "course"]  
        read_only_fields = ["id"]