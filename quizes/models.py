from django.db import models
from courses.models import Course 
from django.conf import settings



class Quiz(models.Model):
    course = models.ForeignKey(Course, related_name='quizzes', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.name} - {self.title}"


class Question(models.Model):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice'),
        ('TEXT', 'Text/Short Answer'),
        ('TF', 'True/False'),
    )
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='MCQ')
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='quiz_attempts', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='attempts', on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.quiz.title}"


class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    text_answer = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.attempt.user.full_name} - {self.question.text[:30]}"
