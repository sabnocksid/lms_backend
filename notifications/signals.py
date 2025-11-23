from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.utils import send_realtime_notification

from courses.models import Course
from lessons.models import Chapter 
from quizes.models import Quiz     

from gramafication.models import PointTransaction, CourseGamification, Enrollment, LearnerProfile

User = get_user_model()


def notify_users(notifications):

    if not notifications:
        return

    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    for notification in notifications:
        send_realtime_notification(notification)



@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    if not created:
        return

    # Notify all learners (users with LearnerProfile)
    students = User.objects.filter(learnerprofile__isnull=False).select_related('learnerprofile')
    
    notifications = [
        Notification(
            recipient=student,
            actor=instance.instructor,
            verb="published a new course",
            target_course=instance,
        )
        for student in students
    ]
    
    notify_users(notifications)




@receiver(post_save, sender=Chapter)
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.lesson.course  
    students = User.objects.filter(learnerprofile__isnull=False)

    notifications = [
        Notification(
            recipient=student,
            actor=course.instructor,
            verb=f"added a new chapter: '{instance.title}'",
            target_course=course,
        )
        for student in students
    ]
    
    notify_users(notifications)



@receiver(post_save, sender=Quiz)
def notify_new_quiz(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.course
    students = User.objects.filter(learnerprofile__isnull=False)

    notifications = [
        Notification(
            recipient=student,
            actor=course.instructor,
            verb=f"added a new quiz: '{instance.title}'",
            target_course=course,
        )
        for student in students
    ]
    
    notify_users(notifications)




@receiver(post_save, sender=Enrollment)
def notify_enrollment(sender, instance, created, **kwargs):
    if not created:
        return

    learner_user = instance.learner.user
    course = instance.course
    instructor = getattr(course, "instructor", None)

    notifications_to_send = []

    if instructor and instructor != learner_user:
        instructor_notif = Notification(
            recipient=instructor,
            actor=learner_user,
            verb=f"enrolled in your course '{course.name}'",
            target_course=course,
        )
        notifications_to_send.append(instructor_notif)

    admins = User.objects.filter(is_staff=True)
    admin_notifications = [
        Notification(
            recipient=admin,
            actor=learner_user,
            verb=f"enrolled in course '{course.name}'",
            target_course=course,
        )
        for admin in admins
        if admin != learner_user  
    ]
    notifications_to_send.extend(admin_notifications)

    notify_users(notifications_to_send)




@receiver(post_save, sender=PointTransaction)
def notify_point_transaction(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.points <= 0:
        return

    notif = Notification(
        recipient=instance.learner.user,
        actor=None,
        verb=f"Earned +{instance.points} points!",
        target_course=instance.enrollment.course if hasattr(instance, 'enrollment') else None,
    )
    Notification.objects.create(notif)  
    send_realtime_notification(notif)



@receiver(post_save, sender=CourseGamification)
def notify_course_completed(sender, instance, updated_fields=None, **kwargs):
    if not instance.course_completed:
        return

    if updated_fields and 'course_completed' not in updated_fields:
        return

    enrollment = instance.enrollment
    course = enrollment.course

    notif = Notification(
        recipient=enrollment.learner.user,
        actor=None,
        verb=f"Congratulations! You completed the course '{course.name}'!",
        target_course=course,
    )
    Notification.objects.create(notif)
    send_realtime_notification(notif)