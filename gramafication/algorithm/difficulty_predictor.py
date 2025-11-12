from django.db.models import Avg, F, Case, When, Value, FloatField
from django.utils import timezone
from ..models import CourseGamification, Enrollment
from courses.models import Course
from lessons.models import Chapter, ChapterProgress
from quizes.models import QuizAttempt, Quiz

class DifficultyPredictor:
    def __init__(self, learner):
        self.learner = learner  # learner.profile object
        self.user = learner.user

    def get_learner_skill(self):
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

            # Completed chapters
            completed_chapters = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course,
                completed=True
            ).count()
            total_chap = Chapter.objects.filter(lesson__course=e.course).count()

            # Quizzes
            attempted_quizzes = QuizAttempt.objects.filter(
                user=self.user,
                quiz__course=e.course
            ).count()
            total_quizzes_course = Quiz.objects.filter(course=e.course).count()

            total_quiz += attempted_quizzes
            total_correct += g.correct_answers if g.correct_answers else 0

            if completed_chapters > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                speeds.append(completed_chapters / days)

        quiz_acc = (total_correct / total_quiz * 100) if total_quiz else 50.0
        comp_rate = (enrollments.filter(gamification__course_completed=True).count() / enrollments.count() * 100) if enrollments.count() else 50.0
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.5
        speed_score = min(avg_speed * 100, 100)

        skill = (quiz_acc * 0.4) + (comp_rate * 0.4) + (speed_score * 0.2)
        skill = max(min(skill, 100), 0)
        return skill

    def get_course_difficulty(self, course):
        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0

        gams = CourseGamification.objects.filter(enrollment__in=enrollments)
        completed_count = enrollments.filter(gamification__course_completed=True).count()
        comp_rate = (completed_count / enrollments.count() * 100) if enrollments.count() else 50.0

        avg_acc_result = gams.aggregate(
            acc=Avg(
                Case(
                    When(attempted_quizzes__gt=0, then=(F("correct_answers") * 100.0) / F("attempted_quizzes")),
                    default=Value(0),
                    output_field=FloatField()
                )
            )
        )
        avg_acc = avg_acc_result['acc'] if avg_acc_result['acc'] is not None else 50.0

        times = []
        for e in enrollments.filter(gamification__course_completed=True):
            g = getattr(e, "gamification", None)
            if g:
                days = max((g.last_updated - e.date_enrolled).days, 1)
                times.append(days)

        avg_days = sum(times) / len(times) if times else 30
        time_score = min((avg_days / 60) * 100, 100)

        difficulty = ((100 - comp_rate) * 0.4) + ((100 - avg_acc) * 0.4) + (time_score * 0.2)
        difficulty = max(min(difficulty, 100), 0)
        return difficulty

    def get_difficulty_level(self, gap):
        if gap <= -20: return 1, "Very Easy"
        elif gap <= -5: return 2, "Easy"
        elif gap <= 10: return 3, "Moderate"
        elif gap <= 25: return 4, "Challenging"
        return 5, "Very Challenging"

    def predict(self, course):
        try:
            skill = self.get_learner_skill()
            difficulty = self.get_course_difficulty(course)
            gap = difficulty - skill
            level, name = self.get_difficulty_level(gap)
            success = max(min(100 - gap * 2, 95), 20)
            days = max(int(30 * (difficulty / skill)) if skill > 0 else 30, 7)
            recommendation = ["Perfect for quick learning", "Good match", "Moderate challenge", "Tough", "Very tough"][level-1]

            # Debug logging
            print(f"[Predict] course={course.id}, skill={skill}, difficulty={difficulty}, gap={gap}, level={level}")

            return {
                "level": level,
                "name": name,
                "skill": round(skill, 1),
                "difficulty": round(difficulty, 1),
                "gap": round(gap, 1),
                "success": round(success, 1),
                "days": days,
                "recommendation": recommendation,
            }

        except Exception as e:
            print(f"[Predict Error] course={course.id}, error={e}")
            return {
                "level": 0,
                "name": "Unknown",
                "skill": 0,
                "difficulty": 0,
                "gap": 0,
                "success": 0,
                "days": 0,
                "recommendation": "N/A"
            }

def predict_difficulty(learner, course):
    return DifficultyPredictor(learner).predict(course)
