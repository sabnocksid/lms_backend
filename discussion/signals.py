from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Course
from discussion.models import DiscussionThread

@receiver(post_save, sender=Course)
def create_default_thread(sender, instance, created, **kwargs):
    if created:
        DiscussionThread.objects.create(
            course=instance,
            title="General Discussion",
            creator=instance.instructor  
        )