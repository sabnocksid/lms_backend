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
from lessons.utils.upload_minio import upload_file_to_minio, get_presigned_url

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

    def get(self, request, *args, **kwargs):
        profile = self.get_object() 
        
        if request.user.role == 'student':
            profile_image_url = None
            if profile.profile_image:
                profile_image_url = get_presigned_url(profile.profile_image, request=request)

            return Response({
                "full_name": profile.full_name,
                "profile_image": profile_image_url,  
                "points": profile.points,
                "xp": profile.xp,
                "rank": profile.rank,
                "rank_position": profile.get_rank_position()
            })
        else:
            return Response({
                "full_name": request.user.full_name,
                "role": request.user.role
            })



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
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        all_students = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")

        top_10_serializer = LeaderboardSerializer(all_students[:10], many=True, context={"request": request})

        top_3_serializer = LeaderboardSerializer(all_students[:3], many=True, context={"request": request})

        current_user = getattr(request.user, "learner_profile", None)

        current_user_data = None
        if current_user:
            serializer = LeaderboardSerializer(current_user, context={"request": request})
            current_user_data = serializer.data

        if request.user.role == "student":
            return Response({
                "leaderboard": top_10_serializer.data,
                "current_user": current_user_data
            })
        else:
            return Response({
                "leaderboard": top_10_serializer.data,
                "top_3_learners": top_3_serializer.data
            })





class CourseGamificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        learner = request.user.learner_profile
        course_gamification = get_object_or_404(CourseGamification, learner=learner, course_id=course_id)
        serializer = CourseGamificationSerializer(course_gamification)
        return Response(serializer.data)
