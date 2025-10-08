from rest_framework import serializers
from .models import LearnerProfile, Badge, PointTransaction, LearnerBadge


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = "__all__"


class LearnerBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = LearnerBadge
        fields = ["badge", "earned_at"]


class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ["points", "reason", "created_at"]


class LearnerProfileSerializer(serializers.ModelSerializer):
    earned_badges = LearnerBadgeSerializer(many=True, read_only=True)
    transactions = PointTransactionSerializer(many=True, read_only=True)
    rank_position = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = [
            "id", "user", "full_name", "profile_image", "date_of_birth",
            "joined_date", "points", "level", "xp", "rank",
            "earned_badges", "transactions", "rank_position"
        ]

    def get_rank_position(self, obj):
        return obj.get_rank_position()


class LeaderboardSerializer(serializers.ModelSerializer):
    rank_position = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = ["id", "full_name", "points", "rank", "rank_position"]

    def get_rank_position(self, obj):
        return obj.get_rank_position()
