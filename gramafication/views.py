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
        if self.request.user.role != 'student':
            return None
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile

    def get(self, request, *args, **kwargs):
        if request.user.role != 'student':
            return Response({
                "full_name": request.user.full_name,
                "role": request.user.role
            })
        
        profile = self.get_object()
        profile_image_url = get_presigned_url(profile.profile_image, request=request) if profile.profile_image else None

        return Response({
            "full_name": profile.full_name,
            "profile_image": profile_image_url,  
            "points": profile.points,
            "xp": profile.xp,
            "rank": profile.rank,
            "rank_position": profile.get_rank_position()
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
    


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top_learners = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:10]
        top_serializer = LeaderboardSerializer(top_learners, many=True, context={"request": request})

        current_user = None
        rank = None

        if request.user.role == 'student':
            current_user, _ = LearnerProfile.objects.get_or_create(
                user=request.user,
                defaults={"full_name": request.user.full_name}
            )
            rank = current_user.get_rank_position()

            return Response({
                "leaderboard": top_serializer.data,
                "current_user": {
                    "id": current_user.id,
                    "full_name": current_user.full_name,
                    "profile_image": get_presigned_url(current_user.profile_image, request=request) if current_user.profile_image else None,
                    "points": current_user.points,
                    "xp": current_user.xp,
                    "rank": current_user.rank,
                    "rank_position": rank
                }
            })

        else:
            top_3 = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:3]
            top_3_serializer = LeaderboardSerializer(top_3, many=True, context={"request": request})
            return Response({
                "leaderboard": top_serializer.data,
                "top_3_learners": top_3_serializer.data
            })






class CourseGamificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        learner = request.user.learner_profile
        course_gamification = get_object_or_404(CourseGamification, learner=learner, course_id=course_id)
        serializer = CourseGamificationSerializer(course_gamification)
        return Response(serializer.data)
