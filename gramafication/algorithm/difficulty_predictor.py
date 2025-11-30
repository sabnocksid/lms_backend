from django.utils import timezone
from lessons.models import ChapterProgress, Chapter
from quizes.models import Quiz, QuizAttempt
from gramafication.models import Enrollment, CourseGamification
import math


class DifficultyPredictor:
    """
    Predict difficulty for a learner for a specific course using
    skill metrics + course difficulty + IRT (2PL model).
    """

    def __init__(self, learner):
        self.learner = learner
        self.user = learner.user

    # --------------------------------------------------
    # 1. LEARNER SKILL
    # --------------------------------------------------
    def get_learner_skill(self):

        enrollments = self.learner.enrollments.filter(is_active=True)
        if not enrollments.exists():
            return 50.0  # neutral skill

        total_quiz = 0
        total_correct = 0
        speeds = []

        for e in enrollments:
            g = getattr(e, "gamification", None)
            if not g:
                continue

            completed_chapters = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course,
                completed=True
            ).count()

            total_chap = Chapter.objects.filter(
                lesson__course=e.course
            ).count()

            attempted_quizzes = QuizAttempt.objects.filter(
                user=self.user,
                quiz__course=e.course
            ).count()

            total_quizzes = Quiz.objects.filter(course=e.course).count()

            total_quiz += attempted_quizzes
            total_correct += g.correct_answers

            if completed_chapters > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                speeds.append(completed_chapters / days)

        # Quiz accuracy
        quiz_acc = (total_correct / total_quiz * 100) if total_quiz else 50.0

        # Completion rate
        completed_courses = sum(
            1 for e in enrollments
            if getattr(e, "gamification", None) and e.gamification.course_completed
        )
        comp_rate = (completed_courses / enrollments.count() * 100) if enrollments else 50.0

        # Learning speed
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.5
        speed_score = min(avg_speed * 100, 100)

        # Weighted skill score
        skill = (quiz_acc * 0.4) + (comp_rate * 0.4) + (speed_score * 0.2)
        return max(min(skill, 100), 0)

    # --------------------------------------------------
    # 2. COURSE DIFFICULTY
    # --------------------------------------------------
    def get_course_difficulty(self, course):

        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0

        gams = [
            e.gamification for e in enrollments
            if hasattr(e, "gamification") and e.gamification
        ]

        # Average quiz accuracy
        if gams:
            total_acc = 0
            for g in gams:
                attempted = g.attempted_quizzes or 0
                correct = g.correct_answers or 0
                acc = (correct / attempted * 100) if attempted else 0
                total_acc += acc
            avg_acc = total_acc / len(gams)
        else:
            avg_acc = 50.0

        # Completion rate
        completed_count = sum(g.course_completed for g in gams)
        comp_rate = (completed_count / len(gams) * 100) if gams else 50.0

        # Time score
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

    # --------------------------------------------------
    # 3. IRT (2PL MODEL)
    # --------------------------------------------------
    def irt_probability(self, theta, beta, alpha=1.3):
        """
        2PL IRT:
        P = 1 / (1 + e^(-α(θ - β)))
        """
        return 1 / (1 + math.exp(-alpha * (theta - beta)))

    # --------------------------------------------------
    # 4. Difficulty Levels
    # --------------------------------------------------
    def get_difficulty_level(self, gap):
        if gap <= -20: return 1, "Very Easy"
        elif gap <= -5: return 2, "Easy"
        elif gap <= 10: return 3, "Moderate"
        elif gap <= 25: return 4, "Challenging"
        return 5, "Very Challenging"

    def get_recommendation(self, gap):
        if gap <= -20: return "Perfect for quick learning"
        elif gap <= 0: return "Comfortable challenge"
        elif gap <= 20: return "Moderate challenge"
        else: return "Tough course, stay focused"

    # --------------------------------------------------
    # 5. FINAL PREDICTION
    # --------------------------------------------------
    def predict(self, course):

        skill = self.get_learner_skill()        # 0–100
        difficulty = self.get_course_difficulty(course)  # 0–100

        # Gap for labels
        gap = max(min(difficulty - skill, 50), -50)

        level, name = self.get_difficulty_level(gap)

        # --- IRT Normalization ---
        # Map 0–100 to the standard IRT range (-3 to +3)
        theta = (skill - 50) / 10
        beta = (difficulty - 50) / 10

        # 2PL IRT probability
        irt_prob = self.irt_probability(theta, beta, alpha=1.3)

        # Convert to percentage (rough domain 15% – 95%)
        success = round(15 + irt_prob * 80, 1)

        # Estimated time required
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
