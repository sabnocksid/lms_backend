from rest_framework import viewsets, permissions
from .models import StudentProfile, Badge, StudentProgress, LevelRule
from .serializers import StudentProfileSerializer, BadgeSerializer, StudentProgressSerializer, LevelRuleSerializer

class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class StudentProgressViewSet(viewsets.ModelViewSet):
    queryset = StudentProgress.objects.all()
    serializer_class = StudentProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

class LevelRuleViewSet(viewsets.ModelViewSet):
    queryset = LevelRule.objects.all()
    serializer_class = LevelRuleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
