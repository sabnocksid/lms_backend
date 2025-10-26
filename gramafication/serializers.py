from rest_framework import serializers
from .models import LearnerProfile, Badge, LearnerBadge, PointTransaction, CourseGamification
from lessons.utils.upload_minio import get_presigned_url

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

class CourseGamificationSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = CourseGamification
        fields = [
            "course", "course_title", "points_earned", "xp_earned",
            "chapters_completed", "total_chapters", "quizzes_attempted",
            "total_quizzes", "correct_answers", "course_completed", "last_updated"
        ]

class LearnerProfileSerializer(serializers.ModelSerializer):
    earned_badges = LearnerBadgeSerializer(many=True, read_only=True)
    transactions = PointTransactionSerializer(many=True, read_only=True)
    course_progress = CourseGamificationSerializer(many=True, read_only=True)
    rank_position = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = [
            "id", "user", "full_name", "profile_image", "date_of_birth",
            "joined_date", "points", "xp", "level", "rank",
            "earned_badges", "transactions", "course_progress", "rank_position"
        ]

    def get_rank_position(self, obj):
        return obj.get_rank_position()

    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get("request")
            return get_presigned_url(obj.profile_image, request=request)
        return None


class LeaderboardSerializer(serializers.ModelSerializer):
    rank_position = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = ["id", "full_name", "profile_image", "points", "xp", "rank", "rank_position"]

    def get_rank_position(self, obj):
        all_learners = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")
        current_rank = 0
        last_points = None
        rank_map = {}
        for index, learner in enumerate(all_learners, start=1):
            if learner.points != last_points:
                current_rank = index
            rank_map[learner.id] = current_rank
            last_points = learner.points
        return rank_map.get(obj.id, None)

    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get("request")
            return get_presigned_url(obj.profile_image, request=request)
        return None

