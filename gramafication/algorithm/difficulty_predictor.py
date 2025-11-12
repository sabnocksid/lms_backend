# difficulty.py

from django.utils import timezone
from lessons.models import ChapterProgress, Chapter
from quizes.models import Quiz, QuizAttempt
from gramafication.models import Enrollment, CourseGamification
import math

class DifficultyPredictor:
    """
    Predict difficulty for a learner for a specific course.
    """

    def __init__(self, learner):
        self.learner = learner  # learner.profile object
        self.user = learner.user

    def get_learner_skill(self):
        """
        Calculate learner's skill based on quiz accuracy, course completion, and speed.
        """
        enrollments = self.learner.enrollments.filter(is_active=True)
        if not enrollments.exists():
            return 50.0

        total_quiz = 0
        total_correct = 0
        speeds = []

        for e in enrollments:
            g = getattr(e, "gamification", None)
            if not g:
                continue

            # Chapters completed
            completed_chapters = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course,
                completed=True
            ).count()
            total_chap = Chapter.objects.filter(lesson__course=e.course).count()

            # Quizzes attempted
            attempted_quizzes = QuizAttempt.objects.filter(
                user=self.user,
                quiz__course=e.course
            ).count()
            total_quizzes = Quiz.objects.filter(course=e.course).count()

            total_quiz += attempted_quizzes
            total_correct += g.correct_answers

            # Speed: chapters per day
            if completed_chapters > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                speeds.append(completed_chapters / days)

        # Quiz accuracy
        quiz_acc = (total_correct / total_quiz * 100) if total_quiz else 50.0

        # Completion rate
        completed_courses = sum(1 for e in enrollments if getattr(e, "gamification", None) and e.gamification.course_completed)
        comp_rate = (completed_courses / enrollments.count() * 100) if enrollments.count() else 50.0

        # Speed score
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.5
        speed_score = min(avg_speed * 100, 100)

        # Weighted skill
        skill = (quiz_acc * 0.4) + (comp_rate * 0.4) + (speed_score * 0.2)
        return max(min(skill, 100), 0)

    def get_course_difficulty(self, course):
        """
        Calculate difficulty of a course based on enrolled learners' performance.
        """
        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0

        gams = [e.gamification for e in enrollments if hasattr(e, "gamification")]

        # Average quiz accuracy
        avg_acc = 50.0
        if gams:
            total_acc = 0
            for g in gams:
                attempted = g.attempted_quizzes or 0
                correct = g.correct_answers or 0
                acc = (correct / attempted * 100) if attempted else 0
                total_acc += acc
            avg_acc = total_acc / len(gams)

        # Completion rate
        completed_count = sum(1 for g in gams if g.course_completed)
        comp_rate = (completed_count / len(gams) * 100) if gams else 50.0

        # Time score (days to complete)
        times = []
        for e in enrollments:
            g = getattr(e, "gamification", None)
            if g:
                days = max((g.last_updated - e.date_enrolled).days, 1)
                times.append(days)
        avg_days = sum(times) / len(times) if times else 30
        time_score = min((avg_days / 60) * 100, 100)

        difficulty = ((100 - comp_rate) * 0.4) + ((100 - avg_acc) * 0.4) + (time_score * 0.2)
        return max(min(difficulty, 100), 0)

    def get_difficulty_level(self, gap):
        """
        Map gap to difficulty level and name.
        """
        if gap <= -20: return 1, "Very Easy"
        elif gap <= -5: return 2, "Easy"
        elif gap <= 10: return 3, "Moderate"
        elif gap <= 25: return 4, "Challenging"
        return 5, "Very Challenging"

    def get_recommendation(self, gap):
        """
        Map gap to a friendly recommendation message.
        """
        if gap <= -20: return "Perfect for quick learning"
        elif gap <= 0: return "Comfortable challenge"
        elif gap <= 20: return "Moderate challenge"
        else: return "Tough course, stay focused"

    def predict(self, course):
        """
        Return full difficulty prediction for a learner and course.
        """
        skill = self.get_learner_skill()
        difficulty = self.get_course_difficulty(course)

        # Gap clamped for stability
        gap = max(min(difficulty - skill, 50), -50)

        level, name = self.get_difficulty_level(gap)

        # Success and days
        success = round(20 + 75 / (1 + math.exp(-(-gap/15))), 1)  # outputs 20–95
        days = max(int(7 + 20 * (difficulty / max(skill, 1))), 7)

        recommendation = self.get_recommendation(gap)

        return {
            "level": level,
            "name": name,
            "skill": round(skill, 1),
            "difficulty": round(difficulty, 1),
            "gap": round(gap, 1),
            "success": success,
            "days": days,
            "recommendation": recommendation,
        }


def predict_difficulty(learner, course):

    return DifficultyPredictor(learner).predict(course)
