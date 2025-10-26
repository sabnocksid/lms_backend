from django.utils import timezone
from ..models import LearnerProfile, PointTransaction
from quizes.models import Quiz, QuizAttempt
from lessons.models import Chapter, ChapterProgress

POINTS_PER_CHAPTER = 5
XP_PER_CHAPTER = 3
POINTS_PER_CORRECT_ANSWER = 10
XP_PER_CORRECT_ANSWER = 5
POINTS_COURSE_COMPLETION = 50
XP_COURSE_COMPLETION = 25

def process_course_gamification(user, course):
    learner = user.profile 

    completed_chapters = ChapterProgress.objects.filter(
        user=user, chapter__lesson__course=course, completed=True
    )
    chapter_points = 0
    chapter_xp = 0

    for progress in completed_chapters:
        reason = f"Chapter completed: {progress.chapter.id}"
        if not PointTransaction.objects.filter(learner=learner, reason=reason).exists():
            PointTransaction.objects.create(
                learner=learner,
                points=POINTS_PER_CHAPTER,
                reason=reason
            )
            chapter_points += POINTS_PER_CHAPTER
            chapter_xp += XP_PER_CHAPTER

    quiz_attempts = QuizAttempt.objects.filter(user=user, quiz__course=course)
    correct_answers = 0
    quiz_points = 0
    quiz_xp = 0

    for attempt in quiz_attempts:
        attempt_correct = 0
        for answer in attempt.answers.all():
            question = answer.question
            if question.question_type == "MCQ" and answer.selected_choice and answer.selected_choice.is_correct:
                attempt_correct += 1
            elif question.question_type == "TF" and answer.selected_choice and getattr(question, "is_true", False) == answer.selected_choice.is_correct:
                attempt_correct += 1
        if attempt_correct > 0:
            reason = f"Quiz correct answers: {attempt.quiz.id}"
            if not PointTransaction.objects.filter(learner=learner, reason=reason).exists():
                points = attempt_correct * POINTS_PER_CORRECT_ANSWER
                xp = attempt_correct * XP_PER_CORRECT_ANSWER
                PointTransaction.objects.create(
                    learner=learner,
                    points=points,
                    reason=reason
                )
                quiz_points += points
                quiz_xp += xp
                correct_answers += attempt_correct

    total_chapters = Chapter.objects.filter(lesson__course=course).count()
    total_quizzes = course.quizzes.count()
    course_completed_bonus = False

    if completed_chapters.count() == total_chapters and quiz_attempts.count() == total_quizzes:
        reason = f"Course completed bonus: {course.id}"
        if not PointTransaction.objects.filter(learner=learner, reason=reason).exists():
            PointTransaction.objects.create(
                learner=learner,
                points=POINTS_COURSE_COMPLETION,
                reason=reason
            )
            quiz_points += POINTS_COURSE_COMPLETION
            quiz_xp += XP_COURSE_COMPLETION
            course_completed_bonus = True

    learner.xp += chapter_xp + quiz_xp
    learner.update_rank()
    learner.save(update_fields=["xp", "rank"])

    return {
        "completed_chapters": completed_chapters.count(),
        "total_chapters": total_chapters,
        "completed_quizzes": quiz_attempts.count(),
        "total_quizzes": total_quizzes,
        "correct_answers": correct_answers,
        "points_earned": chapter_points + quiz_points,
        "xp_earned": chapter_xp + quiz_xp,
        "course_completed_bonus": course_completed_bonus,
        "total_points": learner.points,
        "total_xp": learner.xp,
        "current_rank": learner.rank
    }
