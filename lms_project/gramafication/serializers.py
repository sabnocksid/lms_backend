from rest_framework import serializers
from .models import StudentProfile, Badge, StudentProgress, LevelRule

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'

class StudentProfileSerializer(serializers.ModelSerializer):
    badges = BadgeSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = StudentProfile
        fields = ['user', 'points', 'level', 'badges']

class StudentProgressSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    class Meta:
        model = StudentProgress
        fields = '__all__'

class LevelRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelRule
        fields = '__all__'
