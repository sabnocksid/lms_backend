# signals.py or wherever you have these receivers

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.utils import send_realtime_notification

from courses.models import Course
from lessons.models import Chapter
from quizes.models import Quiz
from gramafication.models import PointTransaction, CourseGamification, Enrollment

User = get_user_model()


def notify_users(notifications):
    if not notifications:
        return
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    for n in notifications:
        send_realtime_notification(n)


# =============================
# NEW COURSE / CHAPTER / QUIZ → Notify all learners
# =============================

@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if not created:
        return

    # FIXED: Use 'profile' instead of 'learnerprofile'
    learners = User.objects.filter(profile__isnull=False).select_related('profile')

    notifications = [
        Notification(
            recipient=user,
            actor=instance.instructor,
            verb="published a new course",
            target_course=instance,
        )
        for user in learners
    ]
    notify_users(notifications)


@receiver(post_save, sender=Chapter)
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.lesson.course
    learners = User.objects.filter(profile__isnull=False)

    notifications = [
        Notification(
            recipient=user,
            actor=course.instructor,
            verb=f"added a new chapter: '{instance.title}'",
            target_course=course,
        )
        for user in learners
    ]
    notify_users(notifications)


@receiver(post_save, sender=Quiz)
def notify_new_quiz(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.course
    learners = User.objects.filter(profile__isnull=False)

    notifications = [
        Notification(
            recipient=user,
            actor=course.instructor,
            verb=f"added a new quiz: '{instance.title}'",
            target_course=course,
        )
        for user in learners
    ]
    notify_users(notifications)


# =============================
# ENROLLMENT NOTIFICATIONS
# =============================

@receiver(post_save, sender=Enrollment)
def notify_enrollment(sender, instance, created, **kwargs):
    if not created:
        return

    learner_user = instance.learner.user
    course = instance.course
    instructor = getattr(course, "instructor", None)

    notifications = []

    # Notify instructor
    if instructor and instructor != learner_user:
        notifications.append(
            Notification(
                recipient=instructor,
                actor=learner_user,
                verb=f"enrolled in your course '{course.name}'",
                target_course=course,
            )
        )

    # Notify admins
    for admin in User.objects.filter(is_staff=True):
        if admin != learner_user:
            notifications.append(
                Notification(
                    recipient=admin,
                    actor=learner_user,
                    verb=f"enrolled in '{course.name}'",
                    target_course=course,
                )
            )

    notify_users(notifications)


# =============================
# POINT TRANSACTION & COMPLETION (already correct)
# =============================

@receiver(post_save, sender=PointTransaction)
def notify_point_transaction(sender, instance, created, **kwargs):
    if not created or instance.points <= 0:
        return

    notif = Notification(
        recipient=instance.learner.user,
        actor=None,
        verb=f"Earned +{instance.points} points!",
        target_course=getattr(instance.enrollment, 'course', None),
    )
    Notification.objects.create(notif)
    send_realtime_notification(notif)


@receiver(post_save, sender=CourseGamification)
def notify_course_completed(sender, instance, **kwargs):
    if not instance.course_completed:
        return

    enrollment = instance.enrollment
    course = enrollment.course

    notif = Notification(
        recipient=enrollment.learner.user,
        actor=None,
        verb=f"Congratulations! You completed '{course.name}'!",
        target_course=course,
    )
    Notification.objects.create(notif)
    send_realtime_notification(notif)