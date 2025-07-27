from rest_framework import serializers
from .models import LearningPath, LearningPathCourse
from courses.serializers import CourseSerializer

class LearningPathCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)

    class Meta:
        model = LearningPathCourse
        fields = ['id', 'course', 'order']

class LearningPathSerializer(serializers.ModelSerializer):
    courses = LearningPathCourseSerializer(source='learningpathcourse_set', many=True, read_only=True)

    class Meta:
        model = LearningPath
        fields = ['id', 'title', 'description', 'created_at', 'courses']
