# difficulty.py

from django.utils import timezone
from django.db.models import Avg, Count, Q, F
from lessons.models import ChapterProgress, Chapter
from quizes.models import Quiz, QuizAttempt
from gramafication.models import Enrollment, CourseGamification
import math
from datetime import timedelta


class DifficultyPredictor:
    """
    Enhanced difficulty predictor with improved accuracy and performance.
    """

    def __init__(self, learner):
        self.learner = learner  # learner.profile object
        self.user = learner.user
        self._learner_stats = None  # Cache for learner stats

    def _get_learner_stats(self):
        """Cache learner statistics to avoid repeated queries"""
        if self._learner_stats is None:
            enrollments = self.learner.enrollments.filter(is_active=True).select_related(
                'course', 'gamification'
            )
            self._learner_stats = {
                'enrollments': enrollments,
                'count': enrollments.count()
            }
        return self._learner_stats

    def get_learner_skill(self):
        """
        Calculate learner's skill with improved weighting and normalization.
        Components:
        - Quiz Performance (40%): Accuracy + Consistency
        - Completion Rate (30%): Finished vs Started courses
        - Learning Speed (20%): Chapters completed per day
        - Engagement (10%): Active learning pattern
        """
        stats = self._get_learner_stats()
        enrollments = stats['enrollments']
        
        if not enrollments.exists():
            return 50.0

        # 1. Quiz Performance (40%)
        quiz_metrics = self._calculate_quiz_performance(enrollments)
        quiz_score = quiz_metrics['score']
        
        # 2. Completion Rate (30%)
        completion_score = self._calculate_completion_rate(enrollments)
        
        # 3. Learning Speed (20%)
        speed_score = self._calculate_learning_speed(enrollments)
        
        # 4. Engagement Score (10%)
        engagement_score = self._calculate_engagement(enrollments)

        # Weighted average with experience boost
        base_skill = (
            quiz_score * 0.40 +
            completion_score * 0.30 +
            speed_score * 0.20 +
            engagement_score * 0.10
        )
        
        # Experience boost: More courses = slightly higher confidence
        experience_boost = min(enrollments.count() * 2, 10)
        
        final_skill = base_skill + experience_boost
        return max(min(final_skill, 100), 0)

    def _calculate_quiz_performance(self, enrollments):
        """Calculate quiz accuracy with consistency factor"""
        quiz_attempts = QuizAttempt.objects.filter(
            user=self.user,
            quiz__course__in=[e.course for e in enrollments]
        ).select_related('quiz')
        
        if not quiz_attempts.exists():
            return {'score': 50.0, 'accuracy': 50.0, 'consistency': 0}
        
        # Calculate per-quiz accuracy
        accuracies = []
        for attempt in quiz_attempts:
            if attempt.total_questions > 0:
                accuracy = (attempt.score / attempt.total_questions) * 100
                accuracies.append(accuracy)
        
        if not accuracies:
            return {'score': 50.0, 'accuracy': 50.0, 'consistency': 0}
        
        avg_accuracy = sum(accuracies) / len(accuracies)
        
        # Consistency: Lower standard deviation = more consistent
        if len(accuracies) > 1:
            mean = avg_accuracy
            variance = sum((x - mean) ** 2 for x in accuracies) / len(accuracies)
            std_dev = math.sqrt(variance)
            consistency = max(100 - std_dev, 0)  # Lower deviation = higher consistency
        else:
            consistency = 75  # Single attempt gets moderate consistency
        
        # Combine accuracy with consistency (80% accuracy, 20% consistency)
        quiz_score = (avg_accuracy * 0.8) + (consistency * 0.2)
        
        return {
            'score': quiz_score,
            'accuracy': avg_accuracy,
            'consistency': consistency
        }

    def _calculate_completion_rate(self, enrollments):
        """Calculate course completion rate with recency weight"""
        if not enrollments.exists():
            return 50.0
        
        completed = 0
        recent_completed = 0
        three_months_ago = timezone.now() - timedelta(days=90)
        
        for e in enrollments:
            gam = getattr(e, 'gamification', None)
            if gam and gam.course_completed:
                completed += 1
                # Recent completions weighted higher
                if e.date_enrolled >= three_months_ago:
                    recent_completed += 1
        
        base_rate = (completed / enrollments.count()) * 100
        
        # Boost for recent activity
        recency_boost = (recent_completed / max(completed, 1)) * 10 if completed > 0 else 0
        
        return min(base_rate + recency_boost, 100)

    def _calculate_learning_speed(self, enrollments):
        """Calculate learning speed with normalization"""
        speeds = []
        
        for e in enrollments:
            completed_chapters = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course,
                completed=True
            ).count()
            
            if completed_chapters > 0:
                days = max((timezone.now() - e.date_enrolled).days, 1)
                # Chapters per day
                speed = completed_chapters / days
                speeds.append(speed)
        
        if not speeds:
            return 50.0
        
        avg_speed = sum(speeds) / len(speeds)
        
        # Normalize: 0.5 chapters/day = 50, 1.0 = 75, 2.0 = 100
        # Using logarithmic scale for better distribution
        if avg_speed > 0:
            speed_score = 50 + (math.log(avg_speed + 0.5) * 30)
        else:
            speed_score = 25
        
        return max(min(speed_score, 100), 0)

    def _calculate_engagement(self, enrollments):
        """Calculate engagement based on active learning patterns"""
        if not enrollments.exists():
            return 50.0
        
        recent_activity = 0
        total_days_active = 0
        
        for e in enrollments:
            # Check recent chapter progress
            recent_progress = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course,
                last_accessed__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_progress:
                recent_activity += 1
            
            # Total active days
            enrollment_days = max((timezone.now() - e.date_enrolled).days, 1)
            progress_days = ChapterProgress.objects.filter(
                user=self.user,
                chapter__lesson__course=e.course
            ).values('last_accessed__date').distinct().count()
            
            if enrollment_days > 0:
                activity_ratio = min(progress_days / enrollment_days, 1)
                total_days_active += activity_ratio * 100
        
        # Average engagement
        if enrollments.count() > 0:
            base_engagement = total_days_active / enrollments.count()
            recent_boost = (recent_activity / enrollments.count()) * 20
            return min(base_engagement + recent_boost, 100)
        
        return 50.0

    def get_course_difficulty(self, course):
        """
        Calculate course difficulty with improved metrics.
        Components:
        - Pass Rate (35%): Inverse of completion rate
        - Quiz Difficulty (35%): Average quiz scores
        - Time Investment (20%): Days to complete
        - Dropout Rate (10%): Early abandonments
        """
        enrollments = Enrollment.objects.filter(
            course=course
        ).select_related('gamification').prefetch_related(
            'course__lessons__chapters'
        )
        
        if not enrollments.exists():
            return 50.0  

        pass_score = self._calculate_pass_rate(enrollments)
        
        quiz_difficulty = self._calculate_quiz_difficulty(course, enrollments)
        
        time_score = self._calculate_time_investment(enrollments)
        
        dropout_score = self._calculate_dropout_rate(enrollments)
        
        difficulty = (
            pass_score * 0.35 +
            quiz_difficulty * 0.35 +
            time_score * 0.20 +
            dropout_score * 0.10
        )
        
        return max(min(difficulty, 100), 0)

    def _calculate_pass_rate(self, enrollments):
        total = enrollments.count()
        completed = sum(
            1 for e in enrollments 
            if hasattr(e, 'gamification') and e.gamification.course_completed
        )
        
        if total == 0:
            return 50.0
        
        completion_rate = (completed / total) * 100
        return 100 - completion_rate

    def _calculate_quiz_difficulty(self, course, enrollments):
        quiz_attempts = QuizAttempt.objects.filter(
            quiz__course=course
        )
        
        if not quiz_attempts.exists():
            return 50.0
        
        total_score = 0
        count = 0
        
        for attempt in quiz_attempts:
            if attempt.total_questions > 0:
                score_pct = (attempt.score / attempt.total_questions) * 100
                total_score += score_pct
                count += 1
        
        if count == 0:
            return 50.0
        
        avg_score = total_score / count
        return 100 - avg_score

    def _calculate_time_investment(self, enrollments):
        times = []
        
        for e in enrollments:
            gam = getattr(e, 'gamification', None)
            if gam and gam.course_completed:
                days = max((gam.last_updated - e.date_enrolled).days, 1)
                times.append(days)
        
        if not times:
            return 50.0
        
        avg_days = sum(times) / len(times)
        
        time_score = min((avg_days / 90) * 100, 100)
        return time_score

    def _calculate_dropout_rate(self, enrollments):
        """High early dropout = harder course"""
        total = enrollments.count()
        if total == 0:
            return 50.0
        
        dropouts = 0
        two_weeks_ago = timezone.now() - timedelta(days=14)
        
        for e in enrollments.filter(date_enrolled__lte=two_weeks_ago):
            gam = getattr(e, 'gamification', None)
            if gam:
                total_chapters = Chapter.objects.filter(
                    lesson__course=e.course
                ).count()
                
                if total_chapters > 0:
                    progress_pct = (gam.chapters_completed / total_chapters) * 100
                    if progress_pct < 20:
                        dropouts += 1
        
        dropout_rate = (dropouts / total) * 100
        return dropout_rate

    def get_difficulty_level(self, gap):

        if gap <= -25:
            return 1, "Very Easy"
        elif gap <= -10:
            return 2, "Easy"
        elif gap <= 10:
            return 3, "Moderate"
        elif gap <= 25:
            return 4, "Challenging"
        else:
            return 5, "Very Challenging"

    def get_recommendation(self, gap, success_rate, days):

        if gap <= -25:
            return "Perfect match! You'll breeze through this."
        elif gap <= -10:
            return "Great fit for your skill level. Steady progress expected."
        elif gap <= 0:
            return "Good challenge with high success probability."
        elif gap <= 15:
            if success_rate >= 70:
                return "Moderate challenge. Stay consistent and you'll succeed."
            else:
                return "Challenging but achievable. Plan for dedicated study time."
        elif gap <= 30:
            if success_rate >= 60:
                return "Tough course. Review prerequisites and allocate extra time."
            else:
                return "Very challenging. Consider building foundational skills first."
        else:
            return "Significant challenge. Strongly recommend prerequisites or similar easier courses."

    def predict(self, course):

        skill = self.get_learner_skill()
        difficulty = self.get_course_difficulty(course)

        gap = max(min(difficulty - skill, 60), -60)

        level, name = self.get_difficulty_level(gap)


        success = round(
            15 + (80 / (1 + math.exp(gap / 15))),
            1
        )


        if skill > 10:
            days_factor = difficulty / skill
            days = max(int(14 * days_factor), 7)
        else:
            days = 30  

        recommendation = self.get_recommendation(gap, success, days)

        confidence = self._calculate_prediction_confidence(course)

        return {
            "level": level,
            "name": name,
            "skill": round(skill, 1),
            "difficulty": round(difficulty, 1),
            "gap": round(gap, 1),
            "success": success,
            "days": days,
            "recommendation": recommendation,
            "confidence": confidence,  
        }

    def _calculate_prediction_confidence(self, course):

        stats = self._get_learner_stats()
        learner_enrollments = stats['count']
        
        course_enrollments = Enrollment.objects.filter(course=course).count()
        
        learner_factor = min(learner_enrollments * 10, 50)
        course_factor = min(course_enrollments * 2, 50)    
        
        confidence = learner_factor + course_factor
        return min(confidence, 100)


def predict_difficulty(learner, course):

    return DifficultyPredictor(learner).predict(course)