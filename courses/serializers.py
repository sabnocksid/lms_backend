import base64
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Course, Chapter, Lesson, UserLessonKey

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class LessonSerializer(serializers.ModelSerializer):
    partial_decryption_key = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'chapter', 'title', 'content_type',
            'video_file', 'document', 'content', 'order',
            'partial_decryption_key'
        ]

    @extend_schema_field(serializers.CharField())
    def get_partial_decryption_key(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        key_obj, created = UserLessonKey.objects.get_or_create(user=user, lesson=obj)
        if created:
            full_key = obj.generate_key()
            key_obj.encrypted_key = full_key
            key_obj.save()
        else:
            full_key = key_obj.get_raw_key()

        part_len = (len(full_key) * 3) // 4
        partial_key = full_key[:part_len]
        return base64.b64encode(partial_key).decode('utf-8')
    
class ChapterSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'order', 'lessons']


class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True) 
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_id',
            'created_by',     
            'created_at',
            'updated_at',
            'is_published',
            'chapters'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
