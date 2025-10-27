from rest_framework import serializers
from .models import LearnerProfile, Badge, LearnerBadge, PointTransaction, CourseGamification
from quizes.models import QuizAttempt
from lessons.utils.upload_minio import get_presigned_url
from courses.models import Course
from lessons.models import Chapter
from lessons.models import ChapterProgress

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
    course_progress = serializers.SerializerMethodField()
    rank_position = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = [
            "id",
            "user",
            "full_name",
            "profile_image",
            "date_of_birth",
            "joined_date",
            "points",
            "xp",
            "level",
            "rank",
            "earned_badges",
            "transactions",
            "course_progress",
            "rank_position",
        ]

    def get_rank_position(self, obj):
        return obj.get_rank_position()

    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get("request")
            return get_presigned_url(obj.profile_image, request=request)
        return None

    def get_course_progress(self, obj):
        user = obj.user
        courses = Course.objects.filter(enrolled_students=user)
        result = []

        for course in courses:
            chapters = Chapter.objects.filter(lesson__course=course)
            total_chapters = chapters.count()
            completed_chapters = ChapterProgress.objects.filter(
                user=user, chapter__in=chapters, completed=True
            ).count()

            total_quizzes = course.quizzes.count()
            quizzes_attended = course.quizzes.filter(
                quizprogress__user=user
            ).count()

            result.append({
                "course_id": course.id,
                "course_name": course.name,
                "total_chapters": total_chapters,
                "completed_chapters": completed_chapters,
                "completion_percentage": (completed_chapters / total_chapters * 100) if total_chapters else 0,
                "quizzes_attended": quizzes_attended,
                "total_quizzes": total_quizzes
            })

        return result





class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "completed_at", "answers"]


class CourseGamificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseGamification
        fields = [
            "points_earned",
            "xp_earned",
            "chapters_completed",
            "total_chapters",
            "quizzes_attempted",
            "total_quizzes",
            "correct_answers",
            "course_completed",
        ]


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






#  for dashboard response combined in one

class WelcomeBoxSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    role = serializers.CharField()
    profile_image = serializers.SerializerMethodField()
    points = serializers.IntegerField(required=False)
    xp = serializers.IntegerField(required=False)
    rank = serializers.CharField(required=False)
    rank_position = serializers.IntegerField(required=False)
    total_courses = serializers.IntegerField(required=False)
    total_quizzes = serializers.IntegerField(required=False)
    total_students = serializers.IntegerField(required=False)

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if getattr(obj, "profile_image", None) and request:
            return get_presigned_url(obj.profile_image, request=request)
        return None


class StatsBoxSerializer(serializers.Serializer):
    courses_completed = serializers.IntegerField()
    quizzes_attended = serializers.IntegerField()
    total_questions_attempted = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    total_incorrect = serializers.IntegerField()
    accuracy = serializers.FloatField()


class LeaderboardSerializer(serializers.ModelSerializer):
    rank_position = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = LearnerProfile
        fields = ["id", "full_name", "points", "xp", "rank", "rank_position", "profile_image"]

    def get_rank_position(self, obj):
        return obj.get_rank_position() if obj else None

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.profile_image and request:
            return get_presigned_url(obj.profile_image, request=request)
        return None


class LeaderboardSectionSerializer(serializers.Serializer):
    leaderboard = LeaderboardSerializer(many=True)
    current_user = serializers.DictField(required=False)
    top_3_learners = LeaderboardSerializer(many=True, required=False)


class DashboardSerializer(serializers.Serializer):
    welcome_box = WelcomeBoxSerializer()
    stats_box = StatsBoxSerializer(required=False)  
    leaderboard = LeaderboardSectionSerializer()