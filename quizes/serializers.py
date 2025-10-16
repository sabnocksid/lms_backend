from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, Answer

# Choice serializer
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']

# Question serializers per type
class MCQQuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'question_type', 'marks', 'choices']

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data)
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)
        return question

class TextQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'question_type', 'marks']

class TFQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'question_type', 'marks']

# Quiz serializer (nested read-only)
class QuizSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'time_limit', 'questions']

    def get_questions(self, obj):
        qs = obj.questions.all()
        return QuestionSerializer(qs, many=True).data

# Adaptive Answer serializer
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'selected_choice', 'text_answer']

class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'score', 'completed_at', 'answers']

    def create(self, validated_data):
        user = self.context['request'].user
        answers_data = validated_data.pop('answers')
        attempt = QuizAttempt.objects.create(user=user, **validated_data)
        for answer_data in answers_data:
            Answer.objects.create(attempt=attempt, **answer_data)
        return attempt
