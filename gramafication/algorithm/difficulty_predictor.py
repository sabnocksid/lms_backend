from django.db.models import Avg, F, Case, When, Value, FloatField
from django.utils import timezone
from ..models import CourseGamification, Enrollment
from courses.models import Course

class HybridDifficultyPredictor:
    def __init__(self, learner):
        self.learner = learner

    # Step 1: Global course difficulty based on all learners
    def get_global_difficulty(self, course):
        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0

        gams = CourseGamification.objects.filter(enrollment__in=enrollments)

        avg_quiz_acc = gams.aggregate(
            avg_acc=Avg(
                Case(
                    When(quizzes_attempted__gt=0,
                         then=(F('correct_answers') * 100.0) / F('quizzes_attempted')),
                    default=Value(50.0),
                    output_field=FloatField()
                )
            )
        )['avg_acc'] or 50.0

        avg_completion = gams.aggregate(
            avg_comp=Avg(
                Case(
                    When(total_chapters__gt=0,
                         then=(F('chapters_completed') * 100.0) / F('total_chapters')),
                    default=Value(50.0),
                    output_field=FloatField()
                )
            )
        )['avg_comp'] or 50.0

        avg_time = enrollments.filter(completed=True).aggregate(
            avg_days=Avg(F('completed_at') - F('date_enrolled'))
        )['avg_days']
        avg_time_days = avg_time.days if avg_time else 30

        difficulty = (
            (100 - avg_completion) * 0.4 +
            (100 - avg_quiz_acc) * 0.4 +
            min((avg_time_days / 60) * 100, 100) * 0.2
        )
        return round(max(min(difficulty, 100), 0), 1)

    # Step 2: Learner's personal skill level
    def get_learner_skill(self):
        enrollments = self.learner.enrollments.filter(is_active=True)
        if not enrollments.exists():
            return 50.0

        gams = CourseGamification.objects.filter(enrollment__in=enrollments)
        total_quiz = sum(g.quizzes_attempted for g in gams)
        total_correct = sum(g.correct_answers for g in gams)
        quiz_acc = ((total_correct / total_quiz) * 100) if total_quiz > 0 else 50.0

        completed = enrollments.filter(completed=True).count()
        total = enrollments.count()
        comp_rate = ((completed / total) * 100) if total > 0 else 50.0

        speeds = []
        for e in enrollments:
            if hasattr(e, 'gamification') and e.gamification.chapters_completed > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                speeds.append(e.gamification.chapters_completed / days)
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.5
        speed_score = min(avg_speed * 100, 100)

        skill = (quiz_acc * 0.4) + (comp_rate * 0.4) + (speed_score * 0.2)
        return round(max(min(skill, 100), 0), 1)

    # Step 3: Hybrid difficulty calculation
    def predict(self, course):
        global_diff = self.get_global_difficulty(course)
        learner_skill = self.get_learner_skill()

        hybrid_diff = (global_diff * 0.6) + ((global_diff - learner_skill) * 0.4)
        hybrid_diff = max(min(hybrid_diff, 100), 0)

        gap = hybrid_diff - learner_skill

        level, label = self.map_level(gap)
        success = max(min(100 - abs(gap) * 1.8, 95), 10)

        days = max(int(30 * (hybrid_diff / (learner_skill or 1))), 7)
        rec = self.get_recommendation(level, success)

        return {
            "level": level,
            "name": label,
            "skill": learner_skill,
            "difficulty": round(hybrid_diff, 1),
            "success": round(success, 1),
            "days": days,
            "recommendation": rec,
        }

    def map_level(self, gap):
        if gap <= -20:
            return 1, "Very Easy"
        elif gap <= -5:
            return 2, "Easy"
        elif gap <= 10:
            return 3, "Moderate"
        elif gap <= 25:
            return 4, "Challenging"
        else:
            return 5, "Very Hard"

    def get_recommendation(self, level, success):
        if level == 1:
            return "Perfect for a quick boost!"
        elif level == 2:
            return "A smooth course for your pace."
        elif level == 3:
            return "A balanced challenge."
        elif level == 4:
            return "Push your limits — you can handle it."
        else:
            return "This one’s tough. Prep before you dive in!"

# --- API Layer Integrations ---

def predict_difficulty(learner, course):
    return HybridDifficultyPredictor(learner).predict(course)

def get_recommendations(learner, max_level=3):
    predictor = HybridDifficultyPredictor(learner)
    enrolled = learner.enrollments.values_list('course_id', flat=True)
    courses = Course.objects.exclude(id__in=enrolled).filter(is_active=True)

    results = []
    for course in courses:
        try:
            pred = predictor.predict(course)
            if pred['level'] <= max_level and pred['success'] >= 50:
                results.append({
                    "course": course,
                    "difficulty": pred["name"],
                    "level": pred["level"],
                    "success": pred["success"],
                    "days": pred["days"],
                    "recommendation": pred["recommendation"],
                })
        except Exception as e:
            print(f"Error predicting difficulty for {course.name}: {e}")
            continue

    return sorted(results, key=lambda x: (-x["success"], x["level"]))
