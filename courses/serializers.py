from rest_framework import serializers
from .models import Course, Category, Rating
from lessons.utils.upload_minio import upload_file_to_minio, get_presigned_url
from lessons.serializers import  LessonWithChapterCountSerializer, LessonWithProgressSerializer
from quizes.serializers import QuizSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class CoursePreviewSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructor = serializers.SerializerMethodField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    quizzes_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    chapters_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    lessons = LessonWithProgressSerializer(many=True, read_only=True)  

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "thumbnail",
            "average_rating",
            "instructor",
            "categories",
            "date_added",
            "quizzes_count",
            "lessons_count",
            "chapters_count",
            "completion_percentage",
            "lessons",  
        ]

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get("request")
            return get_presigned_url(str(obj.thumbnail), request=request)
        return None

    def get_instructor(self, obj):
        instructor = obj.instructor
        if not instructor:
            return None

        name = (
            getattr(instructor, "full_name", None)
            or getattr(instructor, "first_name", None)
            or getattr(instructor, "email", None)
            or "Unknown Instructor"
        )

        instructor_data = {
            "id": instructor.id,
            "name": name,
        }

        profile = getattr(instructor, "learner_profile", None)
        if profile and getattr(profile, "profile_image", None):
            request = self.context.get("request")
            instructor_data["profile_image"] = get_presigned_url(
                str(profile.profile_image), request=request
            )
        else:
            instructor_data["profile_image"] = None

        return instructor_data

    def get_quizzes_count(self, obj):
        return obj.quizzes.count()

    def get_lessons_count(self, obj):
        return obj.lessons.count()
    
    def get_chapters_count(self, obj):
        total_chapters = 0
        for lesson in obj.lessons.all():
            total_chapters += lesson.chapters.count()
        return total_chapters

    def get_completion_percentage(self, obj):
        total_lessons = obj.lessons.count()
        if total_lessons == 0:
            return 0

        total_completion_rate = 0

        for lesson in obj.lessons.all():
            lesson_serializer = LessonWithProgressSerializer(lesson, context=self.context)
            lesson_completion_rate = lesson_serializer.data.get('lesson_completion_rate', 0)

            total_completion_rate += lesson_completion_rate

        average_completion_rate = total_completion_rate / total_lessons
        return average_completion_rate if total_lessons > 0 else 0



class CourseDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source="instructor.username", read_only=True)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    lessons = LessonWithProgressSerializer(many=True, read_only=True)  
    quizzes = QuizSerializer(many=True, read_only=True)    

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
            "lessons",
            "quizzes",
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
