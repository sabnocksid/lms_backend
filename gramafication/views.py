from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import LearnerProfile, PointTransaction
from .serializers import LearnerProfileSerializer, LeaderboardSerializer, PointTransactionSerializer


class LearnerProfileListView(generics.ListAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer


class LearnerProfileDetailView(generics.RetrieveAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer


class LeaderboardView(APIView):
    def get(self, request):
        top_learners = LearnerProfile.get_leaderboard()
        serializer = LeaderboardSerializer(top_learners, many=True)
        return Response(serializer.data)


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


class AddPointsView(APIView):
    def post(self, request, learner_id):
        learner = get_object_or_404(LearnerProfile, id=learner_id)
        serializer = PointTransactionSerializer(data=request.data)
        if serializer.is_valid():
            points = serializer.validated_data["points"]
            reason = serializer.validated_data.get("reason", "")
            learner.add_points(points, reason)
            return Response({"message": f"{points} points added to {learner.full_name}"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
