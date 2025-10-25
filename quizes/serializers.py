from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, Answer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'marks', 'is_true', 'choices']



class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    question_is_true = serializers.SerializerMethodField()
    correct = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            'question', 'question_text', 'question_type', 'selected_choice',
            'text_answer', 'question_is_true', 'correct'
        ]

    def get_question_is_true(self, obj):
        return obj.question.is_true

    def get_correct(self, obj):
        if obj.question.question_type == 'MCQ':
            return obj.selected_choice.is_correct if obj.selected_choice else False
        elif obj.question.question_type == 'TF':
            return (obj.selected_choice.is_correct if obj.selected_choice else False) == obj.question.is_true
        return None





class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'time_limit', 'questions_count']

    def get_questions_count(self, obj):
        return obj.questions.count()



class QuizDetailSerializer(serializers.ModelSerializer):
    questions = UserAnswerSerializer(source='questions', many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'time_limit', 'questions']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'selected_choice', 'text_answer']



class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'completed_at', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        attempt = validated_data.pop('attempt', None) or QuizAttempt.objects.create(**validated_data)
        for answer_data in answers_data:
            Answer.objects.update_or_create(
                attempt=attempt,
                question=answer_data['question'],
                defaults={
                    'selected_choice': answer_data.get('selected_choice'),
                    'text_answer': answer_data.get('text_answer')
                }
            )
        return attempt



class QuizResultSerializer(serializers.ModelSerializer):
    mcq_answers = serializers.SerializerMethodField()
    tf_answers = serializers.SerializerMethodField()
    text_answers = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    attempted = serializers.SerializerMethodField()
    total_correct = serializers.SerializerMethodField()
    total_incorrect = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'title',
            'total_questions', 'attempted', 'total_correct', 'total_incorrect',
            'mcq_answers', 'tf_answers', 'text_answers'
        ]

    def get_mcq_answers(self, obj):
        attempt = self.context.get('attempt')
        if not attempt:
            return []
        return UserAnswerSerializer(
            [a for a in attempt.answers.all() if a.question.question_type == 'MCQ'], many=True
        ).data

    def get_tf_answers(self, obj):
        attempt = self.context.get('attempt')
        if not attempt:
            return []
        return UserAnswerSerializer(
            [a for a in attempt.answers.all() if a.question.question_type == 'TF'], many=True
        ).data

    def get_text_answers(self, obj):
        attempt = self.context.get('attempt')
        if not attempt:
            return []
        return UserAnswerSerializer(
            [a for a in attempt.answers.all() if a.question.question_type == 'TEXT'], many=True
        ).data

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_attempted(self, obj):
        attempt = self.context.get('attempt')
        return attempt.answers.count() if attempt else 0

    def get_total_correct(self, obj):
        attempt = self.context.get('attempt')
        if not attempt:
            return 0
        mcq_correct = sum(
            1 for a in attempt.answers.all() if a.question.question_type == 'MCQ' and a.selected_choice and a.selected_choice.is_correct
        )
        tf_correct = sum(
            1 for a in attempt.answers.all() if a.question.question_type == 'TF' and (a.selected_choice.is_correct if a.selected_choice else False) == a.question.is_true
        )
        return mcq_correct + tf_correct

    def get_total_incorrect(self, obj):
        return self.get_attempted(obj) - self.get_total_correct(obj)
