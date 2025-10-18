from rest_framework import serializers
from .models import Course, Category, Rating
from lessons.utils.upload_minio import upload_file_to_minio, get_presigned_url


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class CoursePreviewSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    quizzes_count = serializers.SerializerMethodField()  
    lessons_count = serializers.SerializerMethodField()  

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "average_rating",
            "instructor_name",
            "categories",
            "date_added",
            "quizzes_count",
            "lessons_count",
        ]

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(str(obj.thumbnail), request=request)
        return None

    def get_quizzes_count(self, obj):
        return obj.quizzes.count() 

    def get_lessons_count(self, obj):
        return obj.lessons.count()  



class CourseDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    thumbnail = serializers.SerializerMethodField()

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

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(str(obj.thumbnail), request=request)
        return None


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        source="categories",
        required=False,
    )
    thumbnail_file = serializers.FileField(write_only=True, required=False)
    thumbnail = serializers.SerializerMethodField() 

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "instructor",
            "description",
            "thumbnail_file",  
            "thumbnail",      
            "category_ids",
            "price",
            "is_published",
            "duration",
        ]
        read_only_fields = ["thumbnail"]

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(str(obj.thumbnail), request=request)
        return None

    def create(self, validated_data):
        file_obj = validated_data.pop("thumbnail_file", None)
        categories = validated_data.pop("categories", [])

        course = Course.objects.create(**validated_data)

        if categories:
            course.categories.set(categories)

        if file_obj:
            key = upload_file_to_minio(file_obj, f"courses/thumbnails/{file_obj.name}")
            if not key:
                raise serializers.ValidationError({"thumbnail_file": "Upload failed!"})
            course.thumbnail = key
            course.save()

        return course

    def update(self, instance, validated_data):
        file_obj = validated_data.pop("thumbnail_file", None)
        categories = validated_data.pop("categories", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if categories is not None:
            instance.categories.set(categories)

        if file_obj:
            key = upload_file_to_minio(file_obj, f"courses/thumbnails/{file_obj.name}")
            if not key:
                raise serializers.ValidationError({"thumbnail_file": "Upload failed!"})
            instance.thumbnail = key

        instance.save()
        return instance


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "points", "course"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = self.context["request"].user
        course = validated_data.get("course")
        if not course:
            raise serializers.ValidationError({"course": "Course must be provided"})
        return Rating.objects.create(user=user, course=course, **validated_data)
