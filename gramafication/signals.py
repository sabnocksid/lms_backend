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
def notify_course(sender, instance, created, **kwargs):
    if not created:
        return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(recipient=s, actor=getattr(instance, "instructor", None),
                     verb="New course added", target_course=instance)
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        send_realtime_notification(n)

@receiver(post_save, sender=Chapter)
def notify_chapter(sender, instance, created, **kwargs):
    if not created:
        return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(recipient=s, actor=getattr(instance.course, "instructor", None),
                     verb=f"New chapter '{instance.title}' added", target_course=instance.course)
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        send_realtime_notification(n)

@receiver(post_save, sender=Quiz)
def notify_quiz(sender, instance, created, **kwargs):
    if not created:
        return
    students = User.objects.filter(profile__role="student")
    notifications = [
        Notification(recipient=s, actor=getattr(instance.course, "instructor", None),
                     verb=f"New quiz '{instance.title}' added", target_course=instance.course)
        for s in students
    ]
    Notification.objects.bulk_create(notifications)
    for n in notifications:
        send_realtime_notification(n)
