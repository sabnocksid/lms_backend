from rest_framework import serializers
from .models import Course, Lesson, Video, Enrollment


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'lesson', 'video_file', 'duration', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__' 

class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    course = serializers.StringRelatedField()

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'enrolled_at']
