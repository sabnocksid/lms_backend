from rest_framework import serializers
from .models import DiscussionThread, DiscussionPost

class DiscussionPostSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source="creator.username", read_only=True)
    
    class Meta:
        model = DiscussionPost
        fields = ["id", "creator", "creator_name", "content", "created_at", "parent"]


class DiscussionThreadSerializer(serializers.ModelSerializer):
    ws_url = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionThread
        fields = ["id", "course", "title", "creator", "created_at", "updated_at", "ws_url"]

    def get_ws_url(self, obj):
        request = self.context.get("request")
        if not request:
            return f"ws://localhost:8001/ws/discussion/{obj.id}/"

        scheme = "wss" if request.is_secure() else "ws"

        host = request.get_host() 

        ws_url = f"{scheme}://{host}/ws/discussion/{obj.id}/"
        return ws_url