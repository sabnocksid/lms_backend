"""
Compact Course Difficulty Prediction Algorithm - FIXED VERSION

STEPS:
1. Learner Skill = (Quiz_Accuracy × 0.4) + (Completion_Rate × 0.4) + (Speed × 0.2)
2. Course Difficulty = (100 - Avg_Completion) × 0.4 + (100 - Avg_Accuracy) × 0.4 + (Time × 0.2)
3. Gap = Difficulty - Skill → Map to Level (1-5)
4. Success = 100 - (Gap × 2), Days = 30 × (Difficulty/Skill)
"""

from django.db.models import Avg, F, Case, When, Value, FloatField, Q
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
        
        # Quiz accuracy
        total_quiz = sum(g.quizzes_attempted for g in gams)
        total_correct = sum(g.correct_answers for g in gams)
        quiz_acc = ((total_correct / total_quiz) * 100) if total_quiz > 0 else 50.0
        
        # Completion rate
        completed = enrollments.filter(completed=True).count()
        total_enrollments = enrollments.count()
        comp_rate = ((completed / total_enrollments) * 100) if total_enrollments > 0 else 50.0
        
        # Speed calculation
        speeds = []
        for e in enrollments:
            if hasattr(e, 'gamification') and e.gamification.chapters_completed > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                speeds.append(e.gamification.chapters_completed / days)
        
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            speed_score = min((avg_speed / 1.0) * 100, 100)
        else:
            speed_score = 50.0
        
        skill = (quiz_acc * 0.4) + (comp_rate * 0.4) + (speed_score * 0.2)
        return max(min(skill, 100.0), 0.0)  # Clamp between 0-100
    
    def get_course_difficulty(self, course):
        """Step 2: Calculate course difficulty (0-100)"""
        enrollments = Enrollment.objects.filter(course=course)
        if not enrollments.exists():
            return 50.0
        
        gams = CourseGamification.objects.filter(enrollment__in=enrollments)
        
        # Completion rate
        completed = enrollments.filter(completed=True).count()
        total_enrollments = enrollments.count()
        comp_rate = ((completed / total_enrollments) * 100) if total_enrollments > 0 else 50.0
        
        # Quiz accuracy - safe division
        avg_acc_result = gams.aggregate(
            acc=Avg(
                Case(
                    When(quizzes_attempted__gt=0,
                         then=(F('correct_answers') * 100.0) / F('quizzes_attempted')),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
        )
        avg_acc = avg_acc_result['acc'] if avg_acc_result['acc'] is not None else 50.0
        
        # Time to complete
        completed_enrollments = enrollments.filter(completed=True)
        times = []
        for e in completed_enrollments:
            if hasattr(e, 'gamification'):
                days = max((e.gamification.last_updated - e.date_enrolled).days, 1)
                times.append(days)
        
        if times:
            avg_days = sum(times) / len(times)
            time_score = min((avg_days / 60) * 100, 100)
        else:
            time_score = 50.0
        
        difficulty = ((100 - comp_rate) * 0.4) + ((100 - avg_acc) * 0.4) + (time_score * 0.2)
        return max(min(difficulty, 100.0), 0.0)  # Clamp between 0-100
    
    def get_difficulty_level(self, gap):
        """Step 3: Map gap to difficulty level"""
        if gap <= -20:
            return 1, "Very Easy"
        elif gap <= -5:
            return 2, "Easy"
        elif gap <= 10:
            return 3, "Moderate"
        elif gap <= 25:
            return 4, "Challenging"
        else:
            return 5, "Very Challenging"
    
    def predict(self, course):
        """Run full prediction"""
        skill = self.get_learner_skill()
        difficulty = self.get_course_difficulty(course)
        gap = difficulty - skill
        
        level, name = self.get_difficulty_level(gap)
        
        # Success rate calculation with bounds
        success = max(min(100 - (gap * 2), 95), 20)
        
        # Days calculation with safe division
        if skill > 0:
            days = max(int(30 * (difficulty / skill)), 7)
        else:
            days = 30
        
        # Recommendation logic
        if level == 1:
            rec = "Perfect for quick learning!"
        elif level == 2:
            rec = "Great match for your skill level"
        elif level == 3:
            rec = "Good challenge" if success >= 70 else "Stay consistent"
        elif level == 4:
            rec = "Tough but achievable" if success >= 60 else "Consider prerequisites"
        else:
            rec = "Very difficult! Build foundations first"
        
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
    """Predict difficulty for a specific course"""
    return DifficultyPredictor(learner).predict(course)


def get_recommendations(learner, max_level=3):
    """Get course recommendations for learner"""
    predictor = DifficultyPredictor(learner)
    enrolled = learner.enrollments.values_list('course_id', flat=True)
    courses = Course.objects.exclude(id__in=enrolled).filter(is_active=True)
    
    results = []
    for course in courses:
        try:
            pred = predictor.predict(course)
            if pred['level'] <= max_level and pred['success'] >= 50:  # Filter out too hard courses
                results.append({
                    'course': course,
                    'difficulty': pred['name'],
                    'level': pred['level'],
                    'success': pred['success'],
                    'days': pred['days'],
                    'recommendation': pred['recommendation'],
                })
        except Exception as e:
            # Log error but continue with other courses
            print(f"Error predicting difficulty for {course.name}: {e}")
            continue
    
    # Sort by success rate (higher is better) and then by level (lower is better)
    return sorted(results, key=lambda x: (-x['success'], x['level']))


# Debugging function
def debug_prediction(learner, course):
    """Debug prediction with detailed output"""
    predictor = DifficultyPredictor(learner)
    
    skill = predictor.get_learner_skill()
    difficulty = predictor.get_course_difficulty(course)
    
    print(f"=== Debug Info ===")
    print(f"Learner: {learner}")
    print(f"Course: {course}")
    print(f"Learner Skill: {skill:.2f}")
    print(f"Course Difficulty: {difficulty:.2f}")
    
    result = predictor.predict(course)
    print(f"\n=== Prediction ===")
    for key, value in result.items():
        print(f"{key}: {value}")
    
    return result


# Example usage
"""
from accounts.models import LearnerProfile
from courses.models import Course

learner = LearnerProfile.objects.get(id=1)
course = Course.objects.get(id=5)

# Basic prediction
result = predict_difficulty(learner, course)
print(f"{result['name']} - {result['success']}% success in {result['days']} days")
print(result['recommendation'])

# Debug mode
debug_result = debug_prediction(learner, course)

# Get recommendations
recs = get_recommendations(learner, max_level=3)
for r in recs[:5]:
    print(f"{r['course'].name}: {r['difficulty']} ({r['success']}% in {r['days']} days)")
"""