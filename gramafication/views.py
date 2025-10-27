from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import LearnerProfile, CourseGamification, PointTransaction
from .serializers import (
    LearnerProfileSerializer,
    LeaderboardSerializer,
    CourseGamificationSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser
from lessons.utils.upload_minio import upload_file_to_minio, get_presigned_url
from django.db.models import Count
from .models import LearnerProfile, Course, Quiz
from quizes.models import QuizAttempt
from lessons.models import Chapter, ChapterProgress
from .serializers import DashboardSerializer, LeaderboardSerializer, PointTransactionSerializer
from courses.serializers import CourseSimpleSerializer
from django.db.models import Avg

class LearnerProfileListView(generics.ListAPIView):
    queryset = LearnerProfile.objects.all()
    serializer_class = LearnerProfileSerializer

class LearnerProfileDetailView(generics.RetrieveAPIView):
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.user.role != 'student':
            return None
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.role in ['admin', 'instructor']:
            total_courses = Course.objects.count()
            total_quizzes = Quiz.objects.count()
            total_students = LearnerProfile.objects.filter(user__role='student').count()

            return Response({
                "role": user.role,
                "full_name": user.full_name,
                "total_courses": total_courses,
                "total_quizzes": total_quizzes,
                "total_students": total_students,
            })

        profile = self.get_object()
        profile_image_url = get_presigned_url(profile.profile_image, request=request) if profile.profile_image else None

        completed_courses = 0
        all_courses = Course.objects.all()  

        for course in all_courses:
            total_chapters = Chapter.objects.filter(lesson__course=course).count()
            completed_chapters = ChapterProgress.objects.filter(
                user=user, chapter__lesson__course=course, completed=True
            ).count()

            if total_chapters > 0 and completed_chapters == total_chapters:
                completed_courses += 1

        quiz_attempts = QuizAttempt.objects.filter(user=user)
        total_quizzes_attended = quiz_attempts.count()
        total_correct = 0
        total_incorrect = 0
        total_questions_attempted = 0

        for attempt in quiz_attempts.select_related('quiz').prefetch_related('answers__selected_choice'):
            answers = attempt.answers.all()
            total_questions_attempted += answers.count()
            total_correct += sum(1 for a in answers if a.selected_choice and a.selected_choice.is_correct)
            total_incorrect += sum(1 for a in answers if a.selected_choice and not a.selected_choice.is_correct)

        accuracy = (total_correct / total_questions_attempted * 100) if total_questions_attempted else 0

        return Response({
            "role": user.role,
            "full_name": profile.full_name,
            "profile_image": profile_image_url,
            "points": profile.points,
            "xp": profile.xp,
            "rank": profile.rank,
            "rank_position": profile.get_rank_position(),
            "courses_completed": completed_courses,
            "quizzes_attended": total_quizzes_attended,
            "total_questions_attempted": total_questions_attempted,
            "total_correct": total_correct,
            "total_incorrect": total_incorrect,
            "accuracy": round(accuracy, 2),
        })




class LearnerProfileUpdateView(generics.UpdateAPIView):
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        profile, _ = LearnerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.full_name}
        )
        return profile
    


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top_learners = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:10]
        top_serializer = LeaderboardSerializer(top_learners, many=True, context={"request": request})

        current_user = None
        rank = None

        if request.user.role == 'student':
            current_user, _ = LearnerProfile.objects.get_or_create(
                user=request.user,
                defaults={"full_name": request.user.full_name}
            )
            rank = current_user.get_rank_position()

            return Response({
                "leaderboard": top_serializer.data,
                "current_user": {
                    "id": current_user.id,
                    "full_name": current_user.full_name,
                    "profile_image": get_presigned_url(current_user.profile_image, request=request) if current_user.profile_image else None,
                    "points": current_user.points,
                    "xp": current_user.xp,
                    "rank": current_user.rank,
                    "rank_position": rank
                }
            })

        else:
            top_3 = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:3]
            top_3_serializer = LeaderboardSerializer(top_3, many=True, context={"request": request})
            return Response({
                "leaderboard": top_serializer.data,
                "top_3_learners": top_3_serializer.data
            })






class CourseGamificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        learner = request.user.learner_profile
        course_gamification = get_object_or_404(CourseGamification, learner=learner, course_id=course_id)
        serializer = CourseGamificationSerializer(course_gamification)
        return Response(serializer.data)

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        welcome_data = {"full_name": user.full_name, "role": user.role}
        stats_box_data = None
        profile = None
        profile_image_url = None

        # Admin/Instructor view
        if user.role in ["admin", "instructor"]:
            welcome_data.update({
                "total_courses": Course.objects.count(),
                "total_quizzes": Quiz.objects.count(),
                "total_students": LearnerProfile.objects.filter(user__role='student').count()
            })

        # Student view
        elif user.role == "student":
            profile, _ = LearnerProfile.objects.get_or_create(
                user=user,
                defaults={"full_name": user.full_name}
            )

            profile_image_url = (
                get_presigned_url(profile.profile_image, request=request)
                if profile.profile_image else None
            )

            welcome_data.update({
                "points": profile.points,
                "xp": profile.xp,
                "rank": profile.rank,
                "rank_position": profile.get_rank_position(),
                "profile_image": profile_image_url
            })

            completed_courses = 0
            for course in Course.objects.all():
                total_chapters = Chapter.objects.filter(lesson__course=course).count()
                completed_chapters = ChapterProgress.objects.filter(
                    user=user, chapter__lesson__course=course, completed=True
                ).count()
                if total_chapters > 0 and completed_chapters == total_chapters:
                    completed_courses += 1

            quiz_attempts = QuizAttempt.objects.filter(user=user)
            total_quizzes_attended = quiz_attempts.count()
            total_correct = sum(
                1 for attempt in quiz_attempts.prefetch_related('answers__selected_choice')
                for a in attempt.answers.all()
                if a.selected_choice and a.selected_choice.is_correct
            )
            total_incorrect = sum(
                1 for attempt in quiz_attempts.prefetch_related('answers__selected_choice')
                for a in attempt.answers.all()
                if a.selected_choice and not a.selected_choice.is_correct
            )
            total_questions_attempted = total_correct + total_incorrect
            accuracy = (
                total_correct / total_questions_attempted * 100
                if total_questions_attempted else 0
            )

            stats_box_data = {
                "courses_completed": completed_courses,
                "quizzes_attended": total_quizzes_attended,
                "total_questions_attempted": total_questions_attempted,
                "total_correct": total_correct,
                "total_incorrect": total_incorrect,
                "accuracy": round(accuracy, 2)
            }

        else:
            return Response({"detail": "Invalid role"}, status=403)

        # Get Top Learners for leaderboard
        top_learners = LearnerProfile.objects.filter(
            user__role='student'
        ).order_by("-points", "full_name")[:10]
        top_serializer = LeaderboardSerializer(
            top_learners, many=True, context={"request": request}
        )

        leaderboard_data = {"leaderboard": top_serializer.data}

        # Add current user's data for student role
        if user.role == "student":
            leaderboard_data["current_user"] = {
                "id": profile.id,
                "full_name": profile.full_name,
                "profile_image": profile_image_url,
                "points": profile.points,
                "xp": profile.xp,
                "rank": profile.rank,
                "rank_position": profile.get_rank_position(),
            }
        else:
            top_3 = LearnerProfile.objects.filter(
                user__role='student'
            ).order_by("-points", "full_name")[:3]
            leaderboard_data["top_3_learners"] = LeaderboardSerializer(
                top_3, many=True, context={"request": request}
            ).data

        # Get Recent Point Transactions
        if user.role == "student":
            transactions = PointTransaction.objects.filter(
                learner__user=user
            ).order_by('-created_at')[:5]
        elif user.role == "instructor":
            courses = Course.objects.filter(instructor=user)
            transactions = PointTransaction.objects.filter(
                learner__course__in=courses
            ).select_related("learner__user").order_by('-created_at')[:5]
        else:  # admin
            transactions = PointTransaction.objects.select_related(
                "learner__user"
            ).order_by('-created_at')[:5]

        transactions_data = []
        for t in transactions:
            data = PointTransactionSerializer(t).data
            if user.role in ["admin", "instructor"]:
                learner_name = t.learner.full_name if t.learner else "Unknown"
                data["reason"] = f"{t.reason} by {learner_name}"
            transactions_data.append(data)

        # Get the Latest 5 Courses
        latest_courses = Course.objects.order_by('-date_added')[:5]
        course_serializer = CourseSimpleSerializer(latest_courses, many=True, context={"request": request})
        latest_courses_data = course_serializer.data

        # Get the Most Rated Courses (Using the `average_rating` property and annotate with Avg)
        most_rated_courses = Course.objects.filter(is_published=True) \
            .annotate(average_rating=Avg('ratings__points')) \
            .order_by('-average_rating')[:5]
        
        most_rated_course_serializer = CourseSimpleSerializer(
            most_rated_courses, many=True, context={"request": request}
        )
        most_rated_courses_data = most_rated_course_serializer.data

        # final response
        dashboard_response = {
            "welcome_box": welcome_data,
            "leaderboard": leaderboard_data,
            "recent_activities": transactions_data,
            "latest_courses": latest_courses_data,
            "most_rated_courses": most_rated_courses_data
        }

        if stats_box_data:
            dashboard_response["stats_box"] = stats_box_data

        return Response(dashboard_response)