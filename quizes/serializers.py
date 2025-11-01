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
        fields = ['id', 'text', 'question_type', 'marks', 'answer_is_true', 'choices']


class ChoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']


class QuestionCreateSerializer(serializers.ModelSerializer):
    choices = ChoiceCreateSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['text', 'question_type', 'marks', 'answer_is_true', 'choices']

    def create(self, validated_data):
        choices_data = validated_data.pop('choices', [])
        question = Question.objects.create(**validated_data)
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)
        return question


class QuizCreateSerializer(serializers.ModelSerializer):
    questions = QuestionCreateSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'time_limit', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        quiz = Quiz.objects.create(**validated_data)
        for question_data in questions_data:
            choices = question_data.pop('choices', [])
            question = Question.objects.create(quiz=quiz, **question_data)
            for choice_data in choices:
                Choice.objects.create(question=question, **choice_data)
        return quiz
    

class QuizUpdateSerializer(serializers.ModelSerializer):
    questions = QuestionCreateSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['course', 'title', 'description', 'time_limit', 'questions']

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.time_limit = validated_data.get('time_limit', instance.time_limit)
        instance.save()

        existing_questions = {q.id: q for q in instance.questions.all()}

        sent_question_ids = [q.get('id') for q in questions_data if q.get('id')]

        for q_id, question in existing_questions.items():
            if q_id not in sent_question_ids:
                question.delete()

        for question_data in questions_data:
            choices_data = question_data.pop('choices', [])

            q_id = question_data.get('id')
            if q_id and q_id in existing_questions:
                question = existing_questions[q_id]
                question.text = question_data.get('text', question.text)
                question.question_type = question_data.get('question_type', question.question_type)
                question.marks = question_data.get('marks', question.marks)
                question.save()

                existing_choices = {c.id: c for c in question.choices.all()}
                sent_choice_ids = [c.get('id') for c in choices_data if c.get('id')]

                for c_id, choice in existing_choices.items():
                    if c_id not in sent_choice_ids:
                        choice.delete()

                for choice_data in choices_data:
                    c_id = choice_data.get('id')
                    if c_id and c_id in existing_choices:
                        choice = existing_choices[c_id]
                        choice.text = choice_data.get('text', choice.text)
                        choice.is_correct = choice_data.get('is_correct', choice.is_correct)
                        choice.save()
                    else:
                        Choice.objects.create(question=question, **choice_data)

            else:
                new_question = Question.objects.create(quiz=instance, **question_data)
                for choice_data in choices_data:
                    Choice.objects.create(question=new_question, **choice_data)

        return instance



class QuestionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'marks']


class QuizDetailSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    questions = QuestionBasicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "time_limit", "question_count", "questions"]

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizFullDetailSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "time_limit", "question_count", "questions"]

    def get_question_count(self, obj):
        return obj.questions.count()


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'selected_choice', 'text_answer']


class QuizAttemptSubmitSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = QuizAttempt
        fields = ['answers']

    def create(self, validated_data):
        user = self.context['request'].user
        answers_data = validated_data.pop('answers')
        quiz_id = self.context['view'].kwargs.get('quiz_id')
        quiz = Quiz.objects.get(id=quiz_id)

        attempt = QuizAttempt.objects.create(user=user, quiz=quiz)
        for answer_data in answers_data:
            Answer.objects.create(attempt=attempt, **answer_data)
        return attempt


class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    answer_is_true = serializers.BooleanField(source='question.answer_is_true', read_only=True)
    correct = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'question', 'question_text', 'question_type', 'selected_choice',
            'text_answer', 'answer_is_true', 'correct'
        ]
    
    def get_correct(self, obj):
        return obj.is_correct


from rest_framework import serializers
from quizes.models import Quiz, QuizAttempt

class QuizResultSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    attempted = serializers.SerializerMethodField()
    total_correct = serializers.SerializerMethodField()
    total_incorrect = serializers.SerializerMethodField()
    attempt_id = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    question_results = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'total_questions', 'attempted',
            'total_correct', 'total_incorrect', 'attempt_id',
            'completed_at', 'question_results'
        ]

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_attempted(self, obj):
        attempt = self.context.get('attempt')
        return attempt.answers.count() if attempt else 0

    def get_total_correct(self, obj):
        attempt = self.context.get('attempt')
        if not attempt:
            return 0
        return sum(1 for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct)

    def get_total_incorrect(self, obj):
        return self.get_attempted(obj) - self.get_total_correct(obj)

    def get_attempt_id(self, obj):
        attempt = self.context.get('attempt')
        return attempt.id if attempt else None

    def get_completed_at(self, obj):
        attempt = self.context.get('attempt')
        return attempt.completed_at if attempt else None

    def get_question_results(self, obj):
        attempt = self.context.get('attempt')
        results = []
        if not attempt:
            return results

        for ans in attempt.answers.all():
            if ans.selected_choice or ans.text_answer:
                results.append({
                    'question_id': ans.question.id,
                    'question_text': ans.question.text,
                    'selected_choice': getattr(ans.selected_choice, 'text', None),
                    'is_correct': getattr(ans.selected_choice, 'is_correct', False),
                    'text_answer': ans.text_answer
                })
        return results




from rest_framework import serializers
from quizes.models import Quiz, QuizAttempt

class QuizSummarySerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    attempted = serializers.SerializerMethodField()
    total_correct = serializers.SerializerMethodField()
    total_incorrect = serializers.SerializerMethodField()
    attempt_id = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    time_limit = serializers.IntegerField(read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "total_questions",
            "attempted",
            "total_correct",
            "total_incorrect",
            "attempt_id",
            "completed_at",
            "time_limit",
        ]

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_attempted(self, obj):
        user = self.context["request"].user
        if user.role == "student":
            attempt = self.context.get("attempts_map", {}).get(obj.id)
            return attempt.answers.count() if attempt else 0
        else:
            return sum(a.answers.count() for a in QuizAttempt.objects.filter(quiz=obj))

    def get_total_correct(self, obj):
        user = self.context["request"].user
        if user.role == "student":
            attempt = self.context.get("attempts_map", {}).get(obj.id)
            if not attempt:
                return 0
            return sum(1 for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct)
        else:
            total = 0
            for attempt in QuizAttempt.objects.filter(quiz=obj):
                total += sum(1 for a in attempt.answers.all() if a.selected_choice and a.selected_choice.is_correct)
            return total

    def get_total_incorrect(self, obj):
        return self.get_attempted(obj) - self.get_total_correct(obj)

    def get_attempt_id(self, obj):
        user = self.context["request"].user
        if user.role == "student":
            attempt = self.context.get("attempts_map", {}).get(obj.id)
            return attempt.id if attempt else None
        return None 

    def get_completed_at(self, obj):
        user = self.context["request"].user
        if user.role == "student":
            attempt = self.context.get("attempts_map", {}).get(obj.id)
            return attempt.completed_at if attempt else None
        return None





