from django.utils import timezone
from ..models import LearnerProfile
from quizes.models import Quiz, QuizAttempt
from lessons.models import Chapter, ChapterProgress

POINTS_PER_CHAPTER = 5
XP_PER_CHAPTER = 3
POINTS_PER_CORRECT_ANSWER = 10
XP_PER_CORRECT_ANSWER = 5
POINTS_COURSE_COMPLETION = 50
XP_COURSE_COMPLETION = 25

def process_course_gamification(user, course):
    # Get the learner profile for the user
    learner = user.learner_profile

    # Step 1: Calculate completed chapters
    completed_chapters = ChapterProgress.objects.filter(
        user=user, chapter__lesson__course=course, completed=True
    ).count()

    # Get the total number of chapters in the course
    total_chapters = Chapter.objects.filter(lesson__course=course).count()

    # Calculate points and XP for completed chapters
    chapter_points = completed_chapters * POINTS_PER_CHAPTER
    chapter_xp = completed_chapters * XP_PER_CHAPTER

    # Step 2: Calculate completed quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(user=user, quiz__course=course)
    correct_answers = 0
    total_quizzes = course.quizzes.count()
    completed_quizzes = quiz_attempts.count()

    # Calculate the number of correct answers from quiz attempts
    for attempt in quiz_attempts:
        for answer in attempt.answers.all():
            question = answer.question
            if question.question_type == "MCQ" and answer.selected_choice and answer.selected_choice.is_correct:
                correct_answers += 1
            elif question.question_type == "TF" and answer.selected_choice and getattr(question, "is_true", False) == answer.selected_choice.is_correct:
                correct_answers += 1

    # Calculate points and XP for correct answers
    quiz_points = correct_answers * POINTS_PER_CORRECT_ANSWER
    quiz_xp = correct_answers * XP_PER_CORRECT_ANSWER

    course_completed_bonus = False
    if completed_chapters == total_chapters and completed_quizzes == total_quizzes:
        quiz_points += POINTS_COURSE_COMPLETION
        quiz_xp += XP_COURSE_COMPLETION
        course_completed_bonus = True

    learner.points += chapter_points + quiz_points
    learner.xp += chapter_xp + quiz_xp

    learner.update_rank()

    learner.save(update_fields=["points", "xp", "rank"])

    return {
        "completed_chapters": completed_chapters,
        "total_chapters": total_chapters,
        "completed_quizzes": completed_quizzes,
        "total_quizzes": total_quizzes,
        "correct_answers": correct_answers,
        "points_earned": chapter_points + quiz_points,
        "xp_earned": chapter_xp + quiz_xp,
        "course_completed_bonus": course_completed_bonus,
        "total_points": learner.points,
        "total_xp": learner.xp,
        "current_rank": learner.rank
    }
