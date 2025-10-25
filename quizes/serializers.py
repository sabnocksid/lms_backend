from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, Answer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()
    answer_is_true = serializers.BooleanField(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'marks', 'answer_is_true', 'choices']

    def get_choices(self, obj):
        if obj.question_type == "TEXT":
            return []

        if obj.question_type == "TF":
            return [
                {"text": "True", "is_correct": obj.answer_is_true},
                {"text": "False", "is_correct": not obj.answer_is_true},
            ]

        return ChoiceSerializer(obj.choices.all(), many=True).data


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'time_limit', 'questions']

class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    question_is_true = serializers.BooleanField(source='question.answer_is_true', read_only=True)
    correct = serializers.BooleanField(source='is_correct', read_only=True)

    class Meta:
        model = Answer
        fields = [
            'question', 'question_text', 'question_type', 'selected_choice',
            'text_answer', 'question_is_true', 'correct'
        ]

class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'time_limit', 'questions_count']

    def get_questions_count(self, obj):
        return obj.questions.count()


class QuizUserDetailSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'time_limit', 'answers']

    def get_answers(self, obj):
        user = self.context['request'].user
        attempt = QuizAttempt.objects.filter(quiz=obj, user=user).last()
        if not attempt:
            return []
        return UserAnswerSerializer(attempt.answers.all(), many=True).data
