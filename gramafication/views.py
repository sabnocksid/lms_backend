from rest_framework import generics, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    LearnerProfile, Task, TaskCompletion
)
from .serializers import (
    LearnerProfileSerializer, LeaderboardSerializer,
    TaskSerializer, TaskCompletionSerializer, LearnerProfileUpdateSerializer
)
from courses.permissions import IsInstructorOrAdminOrReadOnly
from rest_framework.permissions import IsAuthenticated
from lessons.utils.upload_minio import upload_file_to_minio
from rest_framework.parsers import MultiPartParser, FormParser



# Learner Profiles
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


# Tasks
class TaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(course__in=user.enrolled_courses.all(), active=True)

class TaskCreateView(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsInstructorOrAdminOrReadOnly]

    def perform_create(self, serializer):
        course = serializer.validated_data.get("course")
        user = self.request.user

        if course.instructor != user and not user.is_staff:
            raise PermissionDenied("Only the instructor of this course can add tasks.")
        
        serializer.save()

class TaskCompletionView(APIView):
    def post(self, request, learner_id, task_id):
        learner = get_object_or_404(LearnerProfile, id=learner_id)
        task = get_object_or_404(Task, id=task_id, active=True)

        completion, created = TaskCompletion.objects.get_or_create(
            learner=learner, task=task
        )

        serializer = TaskCompletionSerializer(completion)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# Leaderboard
class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_learners = LearnerProfile.get_leaderboard()
        learners = LearnerProfile.objects.order_by("-points", "full_name")

        current_rank = 0
        last_points = None
        rank_map = {}

        for index, learner in enumerate(learners, start=1):
            if learner.points != last_points:
                current_rank = index
            rank_map[learner.id] = current_rank
            last_points = learner.points

        serializer = LeaderboardSerializer(top_learners, many=True)

        try:
            current_user = request.user.learner_profile
            user_rank = rank_map.get(current_user.id)
            user_points = current_user.points
            user_rank_name = current_user.rank

            profile_image = current_user.profile_image
            # Handle both absolute and relative URLs
            if profile_image:
                if str(profile_image).startswith("http"):
                    user_profile_image = profile_image
                else:
                    user_profile_image = request.build_absolute_uri(profile_image)
            else:
                user_profile_image = None

        except LearnerProfile.DoesNotExist:
            current_user = None
            user_rank = None
            user_points = None
            user_rank_name = None
            user_profile_image = None

        return Response({
            "leaderboard": serializer.data,
            "current_user": {
                "id": current_user.id if current_user else None,
                "full_name": current_user.full_name if current_user else None,
                "profile_image": user_profile_image,
                "points": user_points,
                "rank": user_rank_name,
                "rank_position": user_rank,
            },
        })


# Individual learner rank + leaderboard
class LearnerRankView(APIView):
    def get(self, request, learner_id):
        learner = get_object_or_404(LearnerProfile, id=learner_id)
        serializer = LearnerProfileSerializer(learner)
        leaderboard = LearnerProfile.get_leaderboard(top_n=10)
        leaderboard_serializer = LeaderboardSerializer(leaderboard, many=True)
        return Response({
            "learner_profile": serializer.data,
            "global_leaderboard": leaderboard_serializer.data,
        })


class LearnerProfileUpdateView(generics.UpdateAPIView):
    serializer_class = LearnerProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  

    def get_object(self):
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context