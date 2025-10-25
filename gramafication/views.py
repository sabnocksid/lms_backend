from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import LearnerProfile, CourseGamification
from .serializers import (
    LearnerProfileSerializer,
    LeaderboardSerializer,
    CourseGamificationSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser
from lessons.utils.upload_minio import upload_file_to_minio

class LearnerProfileListView(generics.ListAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer

class LearnerProfileDetailView(generics.RetrieveAPIView):
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile

class LearnerProfileUpdateView(generics.UpdateAPIView):
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile

class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top_learners = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:10]
        serializer = LeaderboardSerializer(top_learners, many=True, context={"request": request})

        current_user = None
        rank = None
        if hasattr(request.user, 'learner_profile'):
            try:
                current_user = request.user.learner_profile
                rank = current_user.get_rank_position()
            except LearnerProfile.DoesNotExist:
                current_user = None
                rank = None

        return Response({
            "leaderboard": serializer.data,
            "current_user": {
                "id": current_user.id if current_user else None,
                "full_name": current_user.full_name if current_user else None,
                "points": current_user.points if current_user else None,
                "xp": current_user.xp if current_user else None,
                "rank": current_user.rank if current_user else None,
                "rank_position": rank
            }
        })

class CourseGamificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        learner = request.user.learner_profile
        course_gamification = get_object_or_404(CourseGamification, learner=learner, course_id=course_id)
        serializer = CourseGamificationSerializer(course_gamification)
        return Response(serializer.data)
