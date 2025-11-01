from django.core.management.base import BaseCommand
from gramafication.algorithm.gramafication_course import process_course_gamification
from courses.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Update points and XP for all users based on their completed courses and quizzes.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting points and XP update...\n")

        for user in User.objects.all():
            for course in Course.objects.all():
                result = process_course_gamification(user, course)
                self.stdout.write(f"Updated {user.email} for course {course.name}:\n")
                self.stdout.write(f"Points Earned: {result['points_earned']}, XP Earned: {result['xp_earned']}\n")
        
        self.stdout.write("Points and XP update complete.\n")
