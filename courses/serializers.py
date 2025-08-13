import base64
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Course, Chapter, Lesson, UserLessonKey
import boto3
from botocore.client import Config
from django.conf import settings

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class LessonSerializer(serializers.ModelSerializer):
    partial_decryption_key = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()

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

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_video_file(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        client_partial_key = request.query_params.get("partial_decryption_key")
        if not client_partial_key:
            return None

        try:
            decoded_client_key = base64.b64decode(client_partial_key.encode()).decode()
        except Exception:
            return None  

        try:
            key_obj = UserLessonKey.objects.get(user=user, lesson=obj)
        except UserLessonKey.DoesNotExist:
            return None

        full_key = key_obj.get_raw_key()
        part_len = (len(full_key) * 3) // 4
        expected_partial_key = full_key[:part_len]

        if decoded_client_key != expected_partial_key:
            return None  # Mismatch → do not reveal URL

        if obj.video_file:
            return request.build_absolute_uri(obj.video_file.url) if request else obj.video_file.url

        return None
    

class LessonDetailSerializer(serializers.ModelSerializer):
    partial_decryption_key = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()

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
        return base64.b64encode(partial_key.encode()).decode('utf-8')

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_video_file(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        client_partial_key = request.query_params.get("partial_decryption_key")
        if not client_partial_key:
            return None

        try:
            decoded_client_key = base64.b64decode(client_partial_key.encode()).decode()
        except Exception:
            return None

        try:
            key_obj = UserLessonKey.objects.get(user=user, lesson=obj)
        except UserLessonKey.DoesNotExist:
            return None

        full_key = key_obj.get_raw_key()
        expected_partial_key = full_key[: (len(full_key) * 3) // 4]

        if decoded_client_key != expected_partial_key:
            return None

        if obj.video_file:
            return request.build_absolute_uri(obj.video_file.url)

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

