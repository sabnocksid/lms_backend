from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quiz, QuizAttempt
from .serializers import QuizSerializer, QuizDetailSerializer, QuizResultSerializer, QuizAttemptSerializer
from gramafication.models import PointTransaction
from gramafication.algorithm.gramafication_course import POINTS_PER_CORRECT_ANSWER, XP_PER_CORRECT_ANSWER, POINTS_COURSE_COMPLETION, XP_COURSE_COMPLETION

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        quiz = self.get_object()
        serializer = QuizDetailSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_attempt(self, request, pk=None):
        quiz = self.get_object()
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
        serializer = QuizAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(attempt=attempt)

        self._apply_gramafication(request.user, quiz, attempt)

        return Response({"attempt_id": attempt.id})

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        quiz = self.get_object()
        attempt_id = request.query_params.get('attempt_id')
        attempt = QuizAttempt.objects.get(id=attempt_id, quiz=quiz, user=request.user)
        serializer = QuizResultSerializer(quiz, context={'attempt': attempt})
        return Response(serializer.data)

    def _apply_gramafication(self, user, quiz, attempt):
        learner = getattr(user, 'profile', None)
        if not learner:
            return

        existing_reasons = set(PointTransaction.objects.filter(learner=learner).values_list('reason', flat=True))
        points_earned, xp_earned, correct_answers = 0, 0, 0

        for answer in attempt.answers.all():
            question = answer.question
            reason = f"Quiz {quiz.id} Question {question.id} correct"
            if reason not in existing_reasons:
                is_correct = False
                if question.question_type == 'MCQ' and answer.selected_choice:
                    is_correct = answer.selected_choice.is_correct
                elif question.question_type == 'TF' and answer.selected_choice:
                    is_correct = answer.selected_choice.is_correct == question.is_true
                if is_correct:
                    PointTransaction.objects.create(learner=learner, points=POINTS_PER_CORRECT_ANSWER, reason=reason)
                    points_earned += POINTS_PER_CORRECT_ANSWER
                    xp_earned += XP_PER_CORRECT_ANSWER
                    correct_answers += 1

        if correct_answers == quiz.questions.count():
            bonus_reason = f"Quiz {quiz.id} completed bonus"
            if bonus_reason not in existing_reasons:
                PointTransaction.objects.create(learner=learner, points=POINTS_COURSE_COMPLETION, reason=bonus_reason)
                points_earned += POINTS_COURSE_COMPLETION
                xp_earned += XP_COURSE_COMPLETION

        learner.points += points_earned
        learner.xp += xp_earned
        learner.update_rank()
        learner.save(update_fields=['points', 'xp', 'rank'])
