import base64
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Course, Chapter, Lesson, UserLessonKey
import boto3
from botocore.client import Config
import hashlib
from django.conf import settings

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class LessonSerializer(serializers.ModelSerializer):
    partial_decryption_key = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id',
            'title',
            'partial_decryption_key',
            'order'
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
    


class LessonDetailSerializer(serializers.ModelSerializer):
    partial_decryption_key = serializers.CharField(write_only=True, required=True)
    full_decryption_key = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'chapter', 'title', 'content_type',
            'video_file', 'document', 'content', 'order',
            'partial_decryption_key',  
            'full_decryption_key',     
        ]

    def generate_key_from_user(self, user, lesson):
        user_identifier = getattr(user, 'slug', None) or getattr(user, 'email', None) or str(user.pk)
        key_input = f"{user_identifier}-{lesson.id}"
        return hashlib.sha256(key_input.encode('utf-8')).digest()

    def validate_partial_key(self, partial_key_b64, full_key):
        try:
            partial_key = base64.b64decode(partial_key_b64)
        except Exception:
            return False

        expected_partial_len = (len(full_key) * 3) // 4
        expected_partial_key = full_key[:expected_partial_len]

        return partial_key == expected_partial_key

    def get_full_decryption_key(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        partial_key_b64 = request.query_params.get('partial_decryption_key') if request else None
        if not partial_key_b64:
            return None

        full_key = self.generate_key_from_user(user, obj)
        if not self.validate_partial_key(partial_key_b64, full_key):
            return None

        return base64.b64encode(full_key).decode('utf-8')

    def get_video_file(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        partial_key_b64 = self.initial_data.get('partial_decryption_key')
        if not partial_key_b64:
            return None

        full_key = self.generate_key_from_user(user, obj)
        if not self.validate_partial_key(partial_key_b64, full_key):
            return None

        if obj.video_file:
            return request.build_absolute_uri(obj.video_file.url) if request else obj.video_file.url
        return None

    def get_document(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        partial_key_b64 = self.initial_data.get('partial_decryption_key')
        if not partial_key_b64:
            return None

        full_key = self.generate_key_from_user(user, obj)
        if not self.validate_partial_key(partial_key_b64, full_key):
            return None

        if obj.document:
            return request.build_absolute_uri(obj.document.url) if request else obj.document.url
        return None


class UserLessonKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLessonKey
        fields = ['partial_decryption_key', 'partial_decryption_completed']
    
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

