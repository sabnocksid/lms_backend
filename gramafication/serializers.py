from rest_framework import serializers
from .models import LearnerProfile, Badge, LearnerBadge, PointTransaction, CourseGamification, Enrollment
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
    total_chapters = serializers.ReadOnlyField()
    completed_chapters = serializers.ReadOnlyField()
    total_quizzes = serializers.ReadOnlyField()
    attempted_quizzes = serializers.ReadOnlyField()
    course_completed = serializers.ReadOnlyField()

    class Meta:
        model = CourseGamification
        fields = [
            "points_earned",
            "xp_earned",
            "correct_answers",
            "total_chapters",
            "completed_chapters",
            "total_quizzes",
            "attempted_quizzes",
            "course_completed",
            "last_updated",
        ]



class LearnerProfileSummarySerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = LearnerProfile
        fields = ['full_name', 'profile_image', 'rank', 'level', 'xp']
    
    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            return get_presigned_url(obj.profile_image, request=request)  
        return None




class DetailedPointTransactionSerializer(serializers.ModelSerializer):
    learner_profile = LearnerProfileSummarySerializer(source='learner')

    class Meta:
        model = PointTransaction
        fields = ["id", "points", "reason", "created_at", "learner_profile"]
        

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
        result = []
        enrollments = obj.enrollments.select_related('course').prefetch_related('gamification')
        
        for enrollment in enrollments:
            gamification = getattr(enrollment, 'gamification', None)
            course = enrollment.course
            total_chapters = gamification.total_chapters if gamification else course.lessons.count()
            completed_chapters = gamification.chapters_completed if gamification else 0
            total_quizzes = gamification.total_quizzes if gamification else course.quizzes.count()
            quizzes_attended = gamification.quizzes_attempted if gamification else 0
            points_earned = gamification.points_earned if gamification else 0
            xp_earned = gamification.xp_earned if gamification else 0
            course_completed = gamification.course_completed if gamification else False

            result.append({
                "course_id": course.id,
                "course_name": course.name,
                "total_chapters": total_chapters,
                "completed_chapters": completed_chapters,
                "completion_percentage": (completed_chapters / total_chapters * 100) if total_chapters else 0,
                "quizzes_attended": quizzes_attended,
                "total_quizzes": total_quizzes,
                "points_earned": points_earned,
                "xp_earned": xp_earned,
                "course_completed": course_completed,
                "last_updated": gamification.last_updated if gamification else None,
            })
        return result
    
from lessons.utils.upload_minio import upload_file_to_minio


class LearnerProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image_file = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = LearnerProfile
        fields = ["full_name", "profile_image", "date_of_birth", "profile_image_file"]

    def update(self, instance, validated_data):
        profile_image_file = validated_data.pop("profile_image_file", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_image_file:
            file_name = f"learners/profile_images/{profile_image_file.name}"

            file_url = upload_file_to_minio(profile_image_file, file_name)

            if not file_url:
                raise serializers.ValidationError({"profile_image_file": "Upload failed!"})

            instance.profile_image = file_url

        instance.save()

        return instance





class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "completed_at", "answers"]


class CourseGamificationSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source="enrollment.course.id", read_only=True)
    course_name = serializers.CharField(source="enrollment.course.name", read_only=True)

    class Meta:
        model = CourseGamification
        fields = [
            "course_id",
            "course_name",
            "points_earned",
            "xp_earned",
            "chapters_completed",
            "total_chapters",
            "quizzes_attempted",
            "total_quizzes",
            "correct_answers",
            "course_completed",
            "last_updated",
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


from lessons.models import ChapterProgress
class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.name', read_only=True)
    course_thumbnail = serializers.SerializerMethodField()
    learner_name = serializers.CharField(source='learner.full_name', read_only=True)

    chapters_completed = serializers.SerializerMethodField()
    total_chapters = serializers.SerializerMethodField()
    quizzes_attempted = serializers.SerializerMethodField()
    total_quizzes = serializers.SerializerMethodField()
    course_completed = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'learner_name',
            'course',
            'course_title',
            'course_thumbnail',
            'date_enrolled',
            'is_active',
            'completed',
            'chapters_completed',
            'total_chapters',
            'quizzes_attempted',
            'total_quizzes',
            'course_completed',
        ]

    def get_course_thumbnail(self, obj):
        request = self.context.get("request")
        if obj.course.thumbnail:
            return get_presigned_url(obj.course.thumbnail, request=request)
        return None


    def get_total_chapters(self, obj):
        return Chapter.objects.filter(lesson__course=obj.course).count()

    def get_chapters_completed(self, obj):
        return ChapterProgress.objects.filter(
            learner=obj.learner,
            chapter__lesson__course=obj.course
        ).count()

    def get_total_quizzes(self, obj):
        from quizes.models import Quiz  
        return Quiz.objects.filter(course=obj.course).count()

    def get_quizzes_attempted(self, obj):
        from quizes.models import QuizAttempt
        return QuizAttempt.objects.filter(
            quiz__course=obj.course,
            user=obj.learner.user  
        ).count()

    def get_course_completed(self, obj):
        total_chapters = self.get_total_chapters(obj)
        completed_chapters = self.get_chapters_completed(obj)
        total_quizzes = self.get_total_quizzes(obj)
        attempted_quizzes = self.get_quizzes_attempted(obj)

        if total_chapters == 0 and total_quizzes == 0:
            return False

        chapter_done = completed_chapters >= total_chapters if total_chapters > 0 else True
        quiz_done = attempted_quizzes >= total_quizzes if total_quizzes > 0 else True

        return chapter_done and quiz_done



