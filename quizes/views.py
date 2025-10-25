from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quiz, QuizAttempt, Answer
from .serializers import (
    QuizSerializer, QuizDetailSerializer,
    QuizAttemptSerializer, QuizResultSerializer
)
from gramafication.models import LearnerProfile, PointTransaction
from gramafication.algorithm.gramafication_course import POINTS_PER_CORRECT_ANSWER, XP_PER_CORRECT_ANSWER, POINTS_COURSE_COMPLETION, XP_COURSE_COMPLETION

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizDetailSerializer(quiz)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_attempt(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save(attempt=QuizAttempt.objects.create(user=request.user, quiz=quiz))

        # Gamification integration
        learner = getattr(request.user, 'profile', None)
        if learner:
            points_earned = 0
            xp_earned = 0
            correct_answers = 0

            for answer in attempt.answers.all():
                question = answer.question
                # Check if points already awarded for this question attempt
                existing = PointTransaction.objects.filter(
                    learner=learner,
                    reason=f"Quiz {quiz.id} Question {question.id} correct"
                ).exists()
                if question.question_type in ['MCQ', 'TF']:
                    is_correct = False
                    if question.question_type == 'MCQ' and answer.selected_choice:
                        is_correct = answer.selected_choice.is_correct
                    elif question.question_type == 'TF' and answer.selected_choice:
                        is_correct = answer.selected_choice.is_correct == question.is_true

                    if is_correct and not existing:
                        PointTransaction.objects.create(
                            learner=learner,
                            points=POINTS_PER_CORRECT_ANSWER,
                            reason=f"Quiz {quiz.id} Question {question.id} correct"
                        )
                        points_earned += POINTS_PER_CORRECT_ANSWER
                        xp_earned += XP_PER_CORRECT_ANSWER
                        correct_answers += 1

            # Bonus for completing all quiz questions correctly
            total_questions = quiz.questions.count()
            if correct_answers == total_questions and not PointTransaction.objects.filter(
                learner=learner,
                reason=f"Quiz {quiz.id} completed bonus"
            ).exists():
                PointTransaction.objects.create(
                    learner=learner,
                    points=POINTS_COURSE_COMPLETION,
                    reason=f"Quiz {quiz.id} completed bonus"
                )
                points_earned += POINTS_COURSE_COMPLETION
                xp_earned += XP_COURSE_COMPLETION

            learner.points += points_earned
            learner.xp += xp_earned
            learner.update_rank()
            learner.save(update_fields=['points', 'xp', 'rank'])

        return Response({
            "attempt_id": attempt.id,
            "points_earned": points_earned,
            "xp_earned": xp_earned,
        })

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        quiz = self.get_object()
        attempt_id = request.query_params.get('attempt_id')
        attempt = QuizAttempt.objects.get(id=attempt_id)
        serializer = QuizResultSerializer(quiz, context={'attempt': attempt})
        return Response(serializer.data)
