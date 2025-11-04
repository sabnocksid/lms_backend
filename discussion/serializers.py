from rest_framework import serializers
from .models import DiscussionThread, DiscussionPost

class DiscussionPostSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source="creator.username", read_only=True)
    
    class Meta:
        model = DiscussionPost
        fields = ["id", "creator", "creator_name", "content", "created_at", "parent"]


class DiscussionThreadSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DiscussionThread
        fields = ["id", "course", "title", "creator", "created_at", "updated_at"]