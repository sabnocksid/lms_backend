from rest_framework import serializers
from .models import DiscussionThread, DiscussionPost
from gramafication.serializers import SimpleLearnerSerializer


class DiscussionPostSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source="creator.username", read_only=True)
    
    class Meta:
        model = DiscussionPost
        fields = ["id", "creator", "creator_name", "content", "created_at", "parent"]


class DiscussionThreadSerializer(serializers.ModelSerializer):
    ws_url = serializers.SerializerMethodField()
    discussion_users = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionThread
        fields = [
            "id", 
            "course", 
            "title", 
            "creator", 
            "created_at", 
            "updated_at", 
            "ws_url",
            "discussion_users"
        ]

    def get_ws_url(self, obj):
        request = self.context.get("request")
        if not request:
            return f"ws://localhost:8001/ws/discussion/{obj.id}/"

        scheme = "wss" if request.is_secure() else "ws"
        host = request.get_host()
        ws_url = f"{scheme}://{host}/ws/discussion/{obj.id}/"

        token = request.headers.get("Authorization")
        if token:
            token_value = token.replace("Bearer ", "")
            ws_url = f"{ws_url}?token={token_value}"

        return ws_url

    def get_discussion_users(self, obj):
        enrollments = obj.course.enrollments.filter(is_active=True)
        learners = [enrollment.learner for enrollment in enrollments]

        return SimpleLearnerSerializer(
            learners,
            many=True,
            context=self.context
        ).data
