from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser
from gramafication.models import LearnerProfile

@receiver(post_save, sender=CustomUser)
def create_learner_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'student':
        profile = LearnerProfile.objects.create(
            user=instance,
            full_name=instance.full_name
        )
        instance.learner_profile = profile
        instance.save(update_fields=['learner_profile'])

