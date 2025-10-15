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


# Learner Profiles
class LearnerProfileListView(generics.ListAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer


class LearnerProfileDetailView(generics.RetrieveAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer


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
    def get(self, request):
        top_learners = LearnerProfile.get_leaderboard()
        serializer = LeaderboardSerializer(top_learners, many=True)
        return Response(serializer.data)


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


class UpdateLearnerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            profile = request.user.learner_profile
        except LearnerProfile.DoesNotExist:
            return Response({"error": "Learner profile not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        if 'profile_image_file' in request.FILES:
            file_obj = request.FILES['profile_image_file']
            file_name = f"learners/profile_images/{file_obj.name}"
            key = upload_file_to_minio(file_obj, file_name)
            if key:
                data['profile_image'] = key

        serializer = LearnerProfileUpdateSerializer(profile, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)