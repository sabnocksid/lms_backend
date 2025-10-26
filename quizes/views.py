from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from rest_framework.views import APIView
from django.utils import timezone
from .models import Quiz, QuizAttempt
from .serializers import (
    QuizCreateSerializer,
    QuizFullDetailSerializer,  
    QuizAttemptSubmitSerializer,
    QuizResultSerializer,
    UserAnswerSerializer
)
from gramafication.models import LearnerProfile, CourseGamification, PointTransaction
from gramafication.serializers import CourseGamificationSerializer
from gramafication.algorithm.gramafication_course import process_course_gamification


class QuizCreateAPIView(generics.CreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizFullDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='quiz-detail')  
    def quiz_detail(self, request, pk=None):  
        quiz = self.get_object()
        serializer = QuizFullDetailSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        attempts = QuizAttempt.objects.filter(quiz=quiz, user=user).order_by('-completed_at')
        if not attempts.exists():
            return Response({'detail': 'No attempts found'}, status=404)

        results = [
            QuizResultSerializer(quiz, context={'attempt': attempt}).data
            for attempt in attempts
        ]

        return Response(results)


class QuizAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, quiz_id):
        user = request.user
        learner = user.learner_profile
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get or create QuizAttempt
        attempt = QuizAttempt.objects.create(user=user, quiz=quiz)

        # Award points only if not already awarded
        existing_txn = PointTransaction.objects.filter(
            learner=learner,
            reason=f"Quiz attempt {attempt.id}"
        ).exists()

        if not existing_txn:
            correct_answers = sum(
                1 for ans in attempt.answers.all() 
                if ans.selected_choice and ans.selected_choice.is_correct
            )
            points_earned = correct_answers * 10
            xp_earned = correct_answers * 5

            PointTransaction.objects.create(
                learner=learner,
                points=points_earned,
                reason=f"Quiz attempt {attempt.id}"
            )

            course_progress, _ = CourseGamification.objects.get_or_create(
                learner=learner,
                course=quiz.course,
                defaults={
                    "total_chapters": quiz.course.chapter_count,
                    "total_quizzes": quiz.course.quizzes.count(),
                }
            )
            course_progress.points_earned += points_earned
            course_progress.xp_earned += xp_earned
            course_progress.quizzes_attempted += 1
            course_progress.correct_answers += correct_answers
            course_progress.save()

        serializer = CourseGamificationSerializer(course_progress)
        return Response({
            "attempt_id": attempt.id,
            "quiz_id": quiz.id,
            "submitted_at": attempt.completed_at,
            "gamification": serializer.data
        }, status=status.HTTP_201_CREATED)
