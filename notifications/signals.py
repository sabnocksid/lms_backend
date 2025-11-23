from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.utils import send_realtime_notification

from courses.models import Course
from lessons.models import Chapter
from quizes.models import Quiz

from gramafication.models import PointTransaction, CourseGamification
from gramafication.models import Enrollment

User = get_user_model()

# ---------------------------------------------------
#   COURSE CREATED
# ---------------------------------------------------
@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if not created:
        return

    students = User.objects.filter(profile__role="student")

    notifications = [
        Notification(
            recipient=s,
            actor=instance.instructor,
            verb="added a new course",
            target_course=instance
        )
        for s in students
    ]

    Notification.objects.bulk_create(notifications)

    for n in notifications:
        send_realtime_notification(n)


# ---------------------------------------------------
#   CHAPTER CREATED
# ---------------------------------------------------
@receiver(post_save, sender=Chapter)
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created:
        return

    students = User.objects.filter(profile__role="student")

    notifications = [
        Notification(
            recipient=s,
            actor=instance.lesson.course.instructor,
            verb=f"added a new chapter '{instance.title}'",
            target_course=instance.lesson.course
        )
        for s in students
    ]

    Notification.objects.bulk_create(notifications)

    for n in notifications:
        send_realtime_notification(n)


# ---------------------------------------------------
#   QUIZ CREATED
# ---------------------------------------------------
@receiver(post_save, sender=Quiz)
def notify_new_quiz(sender, instance, created, **kwargs):
    if not created:
        return

    students = User.objects.filter(profile__role="student")

    notifications = [
        Notification(
            recipient=s,
            actor=instance.course.instructor,
            verb=f"added a quiz '{instance.title}'",
            target_course=instance.course
        )
        for s in students
    ]

    Notification.objects.bulk_create(notifications)

    for n in notifications:
        send_realtime_notification(n)


# ---------------------------------------------------
#   NEW ENROLLMENT
# ---------------------------------------------------
@receiver(post_save, sender=Enrollment)
def notify_enrollment(sender, instance, created, **kwargs):
    if not created:
        return

    learner = instance.learner.user
    course = instance.course
    instructor = getattr(course, "instructor", None)

    # Instructor notification
    if instructor:
        notif = Notification.objects.create(
            recipient=instructor,
            actor=learner,
            verb="enrolled in your course",
            target_course=course
        )
        send_realtime_notification(notif)

    # Admin notification
    admins = User.objects.filter(is_staff=True)

    admin_notifs = [
        Notification(
            recipient=a,
            actor=learner,
            verb=f"enrolled in '{course.name}'",
            target_course=course
        )
        for a in admins
    ]

    Notification.objects.bulk_create(admin_notifs)

    for n in admin_notifs:
        send_realtime_notification(n)


# ---------------------------------------------------
#   POINTS EARNED
# ---------------------------------------------------
@receiver(post_save, sender=PointTransaction)
def notify_point_transaction(sender, instance, created, **kwargs):
    if not created:
        return

    learner_user = instance.learner.user

    notif = Notification.objects.create(
        recipient=learner_user,
        actor=None,
        verb=f"{instance.points} points added",
        target_course=None
    )

    send_realtime_notification(notif)


# ---------------------------------------------------
#   COURSE COMPLETED
# ---------------------------------------------------
@receiver(post_save, sender=CourseGamification)
def notify_course_completed(sender, instance, **kwargs):
    if not instance.course_completed:
        return

    enrollment = instance.enrollment
    learner_user = enrollment.learner.user

    notif = Notification.objects.create(
        recipient=learner_user,
        actor=None,
        verb=f"You completed '{enrollment.course.name}'!",
        target_course=enrollment.course
    )

    send_realtime_notification(notif)
