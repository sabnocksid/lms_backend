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
    partial_decryption_key = serializers.SerializerMethodField()
    remaining_partial_key = serializers.SerializerMethodField()  # new field
    video_file = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'chapter', 'title', 'content_type',
            'video_file', 'document', 'content', 'order',
            'partial_decryption_key',
            'remaining_partial_key',
        ]

    def generate_key_from_user(self, user, lesson):
        user_identifier = getattr(user, 'slug', None) or getattr(user, 'email', None) or str(user.pk)
        key_input = f"{user_identifier}-{lesson.id}"
        return hashlib.sha256(key_input.encode('utf-8')).digest()

    def _validate_partial_key(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return False

        client_partial_key = request.query_params.get("partial_decryption_key")
        if not client_partial_key:
            return False

        try:
            decoded_client_key = base64.b64decode(client_partial_key.encode()).decode()
        except Exception:
            return False

        full_key = self.generate_key_from_user(user, obj)
        expected_partial_key = full_key[: (len(full_key) * 3) // 4]

        try:
            expected_partial_key_str = expected_partial_key.decode()
        except UnicodeDecodeError:
            return decoded_client_key.encode() == expected_partial_key
        else:
            return decoded_client_key == expected_partial_key_str

    def get_partial_decryption_key(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        full_key = self.generate_key_from_user(user, obj)
        part_len = (len(full_key) * 3) // 4
        partial_key = full_key[:part_len]
        return base64.b64encode(partial_key).decode('utf-8')

    def get_remaining_partial_key(self, obj):
        if not self._validate_partial_key(obj):
            return None

        request = self.context.get('request')
        user = request.user if request else None
        if not user or user.is_anonymous:
            return None

        full_key = self.generate_key_from_user(user, obj)
        part_len = (len(full_key) * 3) // 4
        remaining_key = full_key[part_len:]
        return base64.b64encode(remaining_key).decode('utf-8')

    def get_video_file(self, obj):
        if self._validate_partial_key(obj) and obj.video_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.video_file.url) if request else obj.video_file.url
        return None

    def get_document(self, obj):
        if self._validate_partial_key(obj) and obj.document:
            request = self.context.get('request')
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

