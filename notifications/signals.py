from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from courses.models import Course
from lessons.models import Chapter
from quizes.models import Quiz
from accounts.models import User
from enrollments.models import Enrollment
from .models import Notification
from .tasks import notify_user_task

User = get_user_model()

# ------------------ STUDENT NOTIFICATIONS ------------------

@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if not created: return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=s,
            actor=getattr(instance, "instructor", None),
            verb="New course added",
            target_course=instance
        )
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        notify_user_task.delay(n.id)

@receiver(post_save, sender=Chapter)
def notify_new_lesson(sender, instance, created, **kwargs):
    if not created: return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=s,
            actor=getattr(instance.course, "instructor", None),
            verb=f"New lesson '{instance.title}' added",
            target_course=instance.course
        )
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        notify_user_task.delay(n.id)

@receiver(post_save, sender=Quiz)
def notify_new_quiz(sender, instance, created, **kwargs):
    if not created: return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(
            recipient=s,
            actor=getattr(instance.course, "instructor", None),
            verb=f"New quiz '{instance.title}' added",
            target_course=instance.course
        )
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        notify_user_task.delay(n.id)

# ------------------ ADMIN NOTIFICATIONS ------------------

@receiver(post_save, sender=User)
def notify_new_user(sender, instance, created, **kwargs):
    if not created: return
    admins = User.objects.filter(profile__role="admin")
    notifications = [
        Notification(
            recipient=a,
            actor=instance,
            verb=f"New user '{instance.username}' registered"
        )
        for a in admins
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        notify_user_task.delay(n.id)

# ------------------ INSTRUCTOR NOTIFICATIONS ------------------

@receiver(post_save, sender=Enrollment)
def notify_instructor_enrollment(sender, instance, created, **kwargs):
    if not created: return
    instructor = instance.course.instructor
    notification = Notification.objects.create(
        recipient=instructor,
        actor=instance.student,
        verb=f"Student '{instance.student.username}' enrolled in your course",
        target_course=instance.course
    )
    notify_user_task.delay(notification.id)
