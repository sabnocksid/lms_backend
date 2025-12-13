from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from notifications.models import Notification
from notifications.tasks import send_notification_task

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.tasks import send_notification_task

User = get_user_model()

def bulk_notify(recipients, actor=None, verb="", course=None):
    notifications = [
        Notification(recipient=user, actor=actor, verb=verb, target_course=course)
        for user in recipients
    ]
    created = Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    for n in created:
        send_notification_task.delay(n.id)


from courses.models import Course
from lessons.models import Chapter
from quizes.models import Quiz
from gramafication.models import Enrollment, PointTransaction, CourseGamification

@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if not created:
        return
    learners = User.objects.filter(profile__isnull=False)
    bulk_notify(
        recipients=learners,
        actor=instance.instructor,
        verb=f"published new course: {instance.name}",
        course=instance
    )

@receiver(post_save, sender=Chapter)
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created:
        return
    course = instance.lesson.course
    learners = User.objects.filter(profile__isnull=False)
    bulk_notify(
        recipients=learners,
        actor=course.instructor,
        verb=f"added chapter: {instance.title}",
        course=course
    )

@receiver(post_save, sender=Quiz)
def notify_new_quiz(sender, instance, created, **kwargs):
    if not created:
        return
    course = instance.course
    learners = User.objects.filter(profile__isnull=False)
    bulk_notify(
        recipients=learners,
        actor=course.instructor,
        verb=f"added quiz: {instance.title}",
        course=course
    )

@receiver(post_save, sender=Enrollment)
def notify_enrollment(sender, instance, created, **kwargs):
    if not created:
        return

    learner = instance.learner.user
    course = instance.course
    instructor = getattr(course, "instructor", None)

    if instructor and instructor != learner:
        n = Notification.objects.create(
            recipient=instructor,
            actor=learner,
            verb=f"enrolled in your course: {course.name}",
            target_course=course
        )
        send_notification_task.delay(n.id)

    for admin in User.objects.filter(is_staff=True):
        if admin != learner:
            n = Notification.objects.create(
                recipient=admin,
                actor=learner,
                verb=f"enrolled in '{course.name}'",
                target_course=course
            )
            send_notification_task.delay(n.id)


@receiver(post_save, sender=PointTransaction)
def notify_points(sender, instance, created, **kwargs):
    if not created or instance.points <= 0:
        return

    n = Notification.objects.create(
        recipient=instance.learner.user,
        verb=f"Earned +{instance.points} points!",
    )
    send_notification_task.delay(n.id)


@receiver(post_save, sender=CourseGamification)
def notify_course_completed(sender, instance, **kwargs):
    if not instance.course_completed:
        return
    if getattr(instance, '_completion_notified', False):
        return
    instance._completion_notified = True

    n = Notification.objects.create(
        recipient=instance.enrollment.learner.user,
        verb=f"Congratulations! You completed '{instance.enrollment.course.name}'!",
        target_course=instance.enrollment.course
    )
    send_notification_task.delay(n.id)
