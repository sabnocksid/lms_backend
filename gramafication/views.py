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


from datetime import timedelta
from django.utils import timezone
import nepali_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from courses.serializers import CoursePreviewSerializer, CourseSimpleSerializer

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        welcome_data = {"full_name": user.full_name, "role": user.role}
        stats_box_data = None
        profile = None
        profile_image_url = None

        today = timezone.localdate()  

        if user.role in ["admin", "instructor"]:
            welcome_data.update({
                "total_courses": Course.objects.count(),
                "total_quizzes": Quiz.objects.count(),
                "total_students": LearnerProfile.objects.filter(user__role='student').count()
            })

            if user.role == "admin":
                students = LearnerProfile.objects.filter(user__role="student")
                student_count = students.count()
            else:
                instructor_courses = Course.objects.filter(instructor=user)
                students = LearnerProfile.objects.filter(
                    chapterprogress__chapter__lesson__course__in=instructor_courses
                ).distinct()

            total_chapters = Chapter.objects.count()
            total_quizzes = Quiz.objects.count()

            performance_trend = []

            for i in range(30):
                day = today - timedelta(days=i)
                next_day = day + timedelta(days=1)
                nepali_date = nepali_datetime.date.from_datetime_date(day)
                bs_date = nepali_date.strftime('%Y-%m-%d')

                # Daily chapter completions
                chapters_completed_today = ChapterProgress.objects.filter(
                    user__in=[s.user for s in students],
                    completed=True,
                    completed_at__gte=day,
                    completed_at__lt=next_day
                ).count()
                course_engagement = chapters_completed_today / total_chapters if total_chapters else 0

                # Daily quiz attempts
                quiz_attempts_today = QuizAttempt.objects.filter(
                    user__in=[s.user for s in students],
                    completed_at__gte=day,
                    completed_at__lt=next_day
                )
                quizzes_attempted = quiz_attempts_today.count()
                quiz_activity = quizzes_attempted / total_quizzes if total_quizzes else 0

                # Accuracy calculation
                total_correct_today = sum(
                    1 for attempt in quiz_attempts_today.prefetch_related("answers__selected_choice")
                    for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct
                )
                total_incorrect_today = sum(
                    1 for attempt in quiz_attempts_today.prefetch_related("answers__selected_choice")
                    for a in attempt.answers.all() if a.selected_choice and not a.selected_choice.is_correct
                )
                total_attempted_today = total_correct_today + total_incorrect_today
                accuracy_today = total_correct_today / total_attempted_today if total_attempted_today else 0

                performance_score = round(
                    (0.4 * course_engagement) + (0.3 * quiz_activity) + (0.3 * accuracy_today), 2
                )
                avg_perf_score =  performance_score / student_count if student_count else 0

                performance_trend.append({
                    "date": str(day),
                    "bs_date": bs_date,
                    "performance_score": performance_score,
                    "course_engagement": round(course_engagement, 2),
                    "quiz_activity": round(quiz_activity, 2),
                    "accuracy_today": round(accuracy_today, 2),
                    "score": round(avg_perf_score, 2),
                })

            # Stats box for admin/instructor: aggregated over all students
            stats_box_data = {
                "performance_last_30_days": list(reversed(performance_trend))
            }

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

            # --- Stats Box ---
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
                for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct
            )
            total_incorrect = sum(
                1 for attempt in quiz_attempts.prefetch_related('answers__selected_choice')
                for a in attempt.answers.all() if a.selected_choice and not a.selected_choice.is_correct
            )
            total_questions_attempted = total_correct + total_incorrect
            accuracy = (total_correct / total_questions_attempted * 100) if total_questions_attempted else 0

            stats_box_data = {
                "courses_completed": completed_courses,
                "quizzes_attended": total_quizzes_attended,
                "total_questions_attempted": total_questions_attempted,
                "total_correct": total_correct,
                "total_incorrect": total_incorrect,
                "accuracy": round(accuracy, 2)
            }

            # --- Performance Trend ---
            performance_trend = []

            for i in range(30):
                day = today - timedelta(days=i)
                next_day = day + timedelta(days=1)
                nepali_date = nepali_datetime.date.from_datetime_date(day)
                bs_date = nepali_date.strftime('%Y-%m-%d')

                chapters_completed_today = ChapterProgress.objects.filter(
                    user=user, completed=True,
                    completed_at__gte=day, completed_at__lt=next_day
                ).count()
                total_chapters = Chapter.objects.count()
                course_engagement = chapters_completed_today / total_chapters if total_chapters else 0

                quiz_attempts_today = QuizAttempt.objects.filter(
                    user=user, completed_at__gte=day,
                    completed_at__lt=next_day
                )
                quizzes_attempted = quiz_attempts_today.count()
                total_quizzes = Quiz.objects.count()
                quiz_activity = quizzes_attempted / total_quizzes if total_quizzes else 0

                total_correct_today = sum(
                    1 for attempt in quiz_attempts_today.prefetch_related("answers__selected_choice")
                    for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct
                )
                total_incorrect_today = sum(
                    1 for attempt in quiz_attempts_today.prefetch_related("answers__selected_choice")
                    for a in attempt.answers.all() if a.selected_choice and not a.selected_choice.is_correct
                )
                total_attempted_today = total_correct_today + total_incorrect_today
                accuracy_today = total_correct_today / total_attempted_today if total_attempted_today else 0

                raw_score = (0.4 * course_engagement) + (0.3 * quiz_activity) + (0.3 * accuracy_today)
                performance_score = round(max(0, min(1.0, raw_score)), 2)

                performance_trend.append({
                    "date": str(day),
                    "bs_date": bs_date,
                    "score": performance_score,
                    "course_engagement": round(course_engagement, 2),
                    "quiz_activity": round(quiz_activity, 2),
                    "accuracy_today": round(accuracy_today, 2)
                })

            performance_trend.reverse()
            stats_box_data["performance_last_30_days"] = performance_trend

        else:
            return Response({"detail": "Invalid role"}, status=403)

        # --- Leaderboard ---
        top_learners = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:10]
        leaderboard_data = {"leaderboard": LeaderboardSerializer(top_learners, many=True, context={"request": request}).data}

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
            top_3 = LearnerProfile.objects.filter(user__role='student').order_by("-points", "full_name")[:3]
            leaderboard_data["top_3_learners"] = LeaderboardSerializer(top_3, many=True, context={"request": request}).data

        # --- Recent Activities ---
        if user.role == "student":
            transactions = PointTransaction.objects.filter(learner__user=user).order_by('-created_at')[:5]
        elif user.role == "instructor":
            courses = Course.objects.filter(instructor=user)
            transactions = PointTransaction.objects.filter(learner__course__in=courses).select_related("learner__user").order_by('-created_at')[:5]
        else:
            transactions = PointTransaction.objects.select_related("learner__user").order_by('-created_at')[:5]

        transactions_data = []
        for t in transactions:
            data = PointTransactionSerializer(t).data
            if user.role in ["admin", "instructor"]:
                learner_name = t.learner.full_name if t.learner else "Unknown"
                data["reason"] = f"{t.reason} by {learner_name}"
            transactions_data.append(data)

        latest_courses = Course.objects.order_by('-date_added')[:5]
        latest_courses_data = CourseSimpleSerializer(latest_courses, many=True, context={"request": request}).data

        continue_watching_data = []
        if user.role == "student":
            continue_watching_courses = (
                Course.objects.prefetch_related("lessons__chapters")
                .annotate(
                    total_chapters=Count("lessons__chapters", distinct=True),
                    completed_chapters=Count(
                        "lessons__chapters__user_progress",
                        filter=Q(
                            lessons__chapters__user_progress__user=user,
                            lessons__chapters__user_progress__completed=True
                        ),
                        distinct=True,
                    ),
                )
                .annotate(
                    completion_percentage=ExpressionWrapper(
                        100 * F("completed_chapters") / F("total_chapters"),
                        output_field=FloatField(),
                    )
                )
                .filter(completion_percentage__lt=100, completion_percentage__gt=0)
                .order_by("-completion_percentage")[:5]
            )

            continue_watching_data = CoursePreviewSerializer(
                continue_watching_courses, many=True, context={"request": request}
            ).data

        top_rated_courses = (
            Course.objects
            .annotate(avg_rating=Avg('ratings__points'))
            .order_by('-avg_rating', '-date_added')[:5]
        )

        highest_rated_courses_data = []
        serializer = CourseSimpleSerializer(top_rated_courses, many=True, context={"request": request})

        for course, data in zip(top_rated_courses, serializer.data):
            # data["average_rating"] = round(course.avg_rating or 0, 2)
            highest_rated_courses_data.append(data)

        dashboard_response = {
            "welcome_box": welcome_data,
            "leaderboard": leaderboard_data,
            "recent_activities": transactions_data,
            "latest_courses": latest_courses_data,
            "highest_rated_courses": highest_rated_courses_data
        }

        if stats_box_data:
            dashboard_response["stats_box"] = stats_box_data

        if continue_watching_data:
            dashboard_response["continue_watching"] = continue_watching_data

        return Response(dashboard_response)
