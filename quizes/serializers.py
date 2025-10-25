from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt, Answer

class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'time_limit']

class QuizSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'course', 'title', 'description', 'time_limit', 'questions_count']

    def get_questions_count(self, obj):
        return obj.questions.count()

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']

class MCQQuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'marks', 'question_type', 'choices']

    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data, question_type='MCQ')
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

class TextQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'marks', 'question_type']

    def create(self, validated_data):
        return Question.objects.create(**validated_data, question_type='TEXT')

class TFQuestionSerializer(serializers.ModelSerializer):
    is_true = serializers.BooleanField(write_only=True)

    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'marks', 'question_type', 'is_true']

    def create(self, validated_data):
        is_true_value = validated_data.pop('is_true')
        question = Question.objects.create(**validated_data, question_type='TF')
        question.is_true = is_true_value
        question.save()
        return question

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
class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    correct = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ['question', 'question_text', 'question_type', 'selected_choice', 'text_answer', 'correct']

    def get_correct(self, obj):
        if obj.question.question_type == 'MCQ':
            return obj.selected_choice.is_correct if obj.selected_choice else False
        elif obj.question.question_type == 'TF':
            return obj.question.is_true == obj.selected_choice.is_correct if obj.selected_choice else False
        elif obj.question.question_type == 'TEXT':
            return None
        return False


class QuizResultSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True)
    total_correct = serializers.SerializerMethodField()
    total_incorrect = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'answers', 'total_correct', 'total_incorrect']

    def __init__(self, *args, **kwargs):
        attempt = kwargs['context'].get('attempt')
        if attempt:
            kwargs['data'] = kwargs.get('data', {})  
            self.answers_qs = attempt.answers.all()
        else:
            self.answers_qs = []
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['answers'] = UserAnswerSerializer(self.answers_qs, many=True).data
        rep['total_correct'] = self.get_total_correct(instance)
        rep['total_incorrect'] = self.get_total_incorrect(instance)
        return rep

    def get_total_correct(self, obj):
        correct_count = 0
        for answer in self.answers_qs:
            if answer.question.question_type == 'MCQ' and answer.selected_choice and answer.selected_choice.is_correct:
                correct_count += 1
            elif answer.question.question_type == 'TF':
                selected = answer.selected_choice
                if selected:
                    correct_count += answer.question.is_true == selected.is_correct
        return correct_count

    def get_total_incorrect(self, obj):
        return len(self.answers_qs) - self.get_total_correct(obj)
