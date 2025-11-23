from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from courses.models import Course
from lessons.models import Chapter
from quizes.models import Quiz
from .models import Notification
from .utils import send_realtime_notification

User = get_user_model()


@receiver(post_save, sender=Course)
def notify_students_course_created(sender, instance, created, **kwargs):
    if not created:
        return

    # get all students
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=student,
            actor=getattr(instance, "instructor", None),
            verb="New course added",
            target_course=instance
        )
        for student in students
    ]
    Notification.objects.bulk_create(notifications)

    # send real-time notifications
    for notification in notifications:
        send_realtime_notification(notification)


@receiver(post_save, sender=Chapter)
def notify_students_chapter_created(sender, instance, created, **kwargs):
    if not created:
        return

    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=student,
            actor=getattr(instance.course, "instructor", None),
            verb=f"New chapter '{instance.title}' added",
            target_course=instance.course
        )
        for student in students
    ]
    Notification.objects.bulk_create(notifications)

    for notification in notifications:
        send_realtime_notification(notification)


@receiver(post_save, sender=Quiz)
def notify_students_quiz_created(sender, instance, created, **kwargs):
    if not created:
        return

    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=student,
            actor=getattr(instance.course, "instructor", None),
            verb=f"New quiz '{instance.title}' added",
            target_course=instance.course
        )
        for student in students
    ]
    Notification.objects.bulk_create(notifications)

    for notification in notifications:
        send_realtime_notification(notification)


@receiver(post_save, sender=User)
def notify_on_new_user(sender, instance, created, **kwargs):
    if not created:
        return

    # notify admins
    admins = User.objects.filter(profile__role="admin")
    admin_notifications = [
        Notification(
            recipient=admin,
            actor=instance,
            verb="New user registered"
        )
        for admin in admins
    ]
    Notification.objects.bulk_create(admin_notifications)
    for notification in admin_notifications:
        send_realtime_notification(notification)

    # notify instructors if student enrolled in courses
    if hasattr(instance, "enrollments"):  # adjust based on your enrollment relation
        instructor_notifications = []
        for enrollment in instance.enrollments.all():
            instructor = enrollment.course.instructor
            instructor_notifications.append(
                Notification(
                    recipient=instructor,
                    actor=instance,
                    verb=f"Student enrolled in '{enrollment.course.name}'",
                    target_course=enrollment.course
                )
            )
        Notification.objects.bulk_create(instructor_notifications)
        for notification in instructor_notifications:
            send_realtime_notification(notification)
