from rest_framework import serializers
from .models import (
    LearnerProfile, Badge, PointTransaction, LearnerBadge,
    Task, TaskCompletion
)

from lessons.utils.upload_minio import upload_file_to_minio

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "description", "icon", "points_required"]


class LearnerBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = LearnerBadge
        fields = ["badge", "earned_at"]


class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ["id", "points", "reason", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "course", "name", "description", "points", "active", "created_at"]


class TaskCompletionSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = TaskCompletion
        fields = ["id", "task", "completed_at", "processed"]


class LearnerProfileSerializer(serializers.ModelSerializer):
    earned_badges = LearnerBadgeSerializer(many=True, read_only=True)
    transactions = PointTransactionSerializer(many=True, read_only=True)
    completed_tasks = TaskCompletionSerializer(many=True, read_only=True)
    rank_position = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = [
            "id", "user", "full_name", "profile_image", "date_of_birth",
            "joined_date", "points", "level", "xp", "rank",
            "earned_badges", "transactions", "completed_tasks", "rank_position"
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



class LearnerProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = LearnerProfile
        fields = ["date_of_birth", "profile_image", "profile_image_file"]
        extra_kwargs = {
            "profile_image": {"read_only": True},  # only set internally after upload
        }

    def update(self, instance, validated_data):
        file_obj = validated_data.pop("profile_image_file", None)

        if file_obj:
            key = upload_file_to_minio(file_obj, f"learners/profile_images/{file_obj.name}")
            instance.profile_image = key  # store public URL in CharField

        if "date_of_birth" in validated_data:
            instance.date_of_birth = validated_data["date_of_birth"]

        instance.save()
        return instance