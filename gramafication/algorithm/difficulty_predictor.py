"""
Compact Course Difficulty Prediction Algorithm

STEPS:
1. Learner Skill = (Quiz_Accuracy × 0.4) + (Completion_Rate × 0.4) + (Speed × 0.2)
2. Course Difficulty = (100 - Avg_Completion) × 0.4 + (100 - Avg_Accuracy) × 0.4 + (Time × 0.2)
3. Gap = Difficulty - Skill → Map to Level (1-5)
4. Success = 100 - (Gap × 2), Days = 30 × (Difficulty/Skill)
"""

from django.db.models import Avg, F
from django.utils import timezone
from ..models import CourseGamification, Enrollment
from courses.models import Course


class DifficultyPredictor:
    
    def __init__(self, learner):
        self.learner = learner
    
    def get_learner_skill(self):
        """Step 1: Calculate learner skill (0-100)"""
        enrollments = self.learner.enrollments.filter(is_active=True)
        if not enrollments.exists():
            return 50.0
        
        gams = CourseGamification.objects.filter(enrollment__in=enrollments)
        
        total_quiz = sum(g.quizzes_attempted for g in gams)
        total_correct = sum(g.correct_answers for g in gams)
        quiz_acc = (total_correct / total_quiz * 100) if total_quiz > 0 else 50
        
        completed = enrollments.filter(completed=True).count()
        comp_rate = (completed / enrollments.count() * 100) if enrollments.count() > 0 else 50
        
        speeds = []
        for e in enrollments:
            if hasattr(e, 'gamification'):
                days = (timezone.now() - e.date_enrolled).days or 1
                speeds.append(e.gamification.chapters_completed / days)
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.5
        speed_score = min(avg_speed / 1.0 * 100, 100)
        
        return quiz_acc * 0.4 + comp_rate * 0.4 + speed_score * 0.2
    
    def get_course_difficulty(self, course):
        """Step 2: Calculate course difficulty (0-100)"""
        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0
        
        gams = CourseGamification.objects.filter(enrollment__in=enrollments)
        
        # Completion rate
        completed = enrollments.filter(completed=True).count()
        comp_rate = (completed / enrollments.count() * 100) if enrollments.count() > 0 else 50
        
        # Quiz accuracy
        avg_acc = gams.aggregate(
            acc=Avg(F('correct_answers') * 100.0 / F('quizzes_attempted'))
        )['acc'] or 50
        
        # Time to complete
        times = []
        for e in enrollments.filter(completed=True):
            if hasattr(e, 'gamification'):
                times.append((e.gamification.last_updated - e.date_enrolled).days)
        avg_days = sum(times) / len(times) if times else 30
        time_score = min(avg_days / 60 * 100, 100)
        
        return (100 - comp_rate) * 0.4 + (100 - avg_acc) * 0.4 + time_score * 0.2
    
    def get_difficulty_level(self, gap):
        """Step 3: Map gap to difficulty level"""
        if gap <= -20: return 1, "Very Easy"
        if gap <= -5: return 2, "Easy"
        if gap <= 10: return 3, "Moderate"
        if gap <= 25: return 4, "Challenging"
        return 5, "Very Challenging"
    
    def predict(self, course):
        """Run full prediction"""
        skill = self.get_learner_skill()
        difficulty = self.get_course_difficulty(course)
        gap = difficulty - skill
        
        level, name = self.get_difficulty_level(gap)
        success = max(min(100 - (gap * 2), 95), 20)
        days = max(int(30 * (difficulty / (skill or 1))), 7)
        
        # Recommendation
        if level == 1: rec = "Perfect for quick learning!"
        elif level == 2: rec = "Great match for your skill level"
        elif level == 3: rec = "Good challenge" if success >= 70 else "Stay consistent"
        elif level == 4: rec = "Tough but achievable" if success >= 60 else "Consider prerequisites"
        else: rec = "Very difficult! Build foundations first"
        
        return {
            'level': level,
            'name': name,
            'skill': round(skill, 1),
            'difficulty': round(difficulty, 1),
            'gap': round(gap, 1),
            'success': round(success, 1),
            'days': days,
            'recommendation': rec,
        }


# Usage functions
def predict_difficulty(learner, course):
    return DifficultyPredictor(learner).predict(course)


def get_recommendations(learner, max_level=3):
    predictor = DifficultyPredictor(learner)
    enrolled = learner.enrollments.values_list('course_id', flat=True)
    courses = Course.objects.exclude(id__in=enrolled)
    
    results = []
    for course in courses:
        pred = predictor.predict(course)
        if pred['level'] <= max_level:
            results.append({
                'course': course,
                'difficulty': pred['name'],
                'success': pred['success'],
                'days': pred['days'],
            })
    
    return sorted(results, key=lambda x: x['success'], reverse=True)


# Example
"""
learner = LearnerProfile.objects.get(id=1)
course = Course.objects.get(id=5)

result = predict_difficulty(learner, course)
print(f"{result['name']} - {result['success']}% success in {result['days']} days")
print(result['recommendation'])

# Get easy-moderate courses
recs = get_recommendations(learner, max_level=3)
for r in recs[:5]:
    print(f"{r['course'].name}: {r['difficulty']} ({r['success']}%)")
"""