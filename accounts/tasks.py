from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse

@shared_task
def send_verification_email(email):
    from .models import CustomUser
    user = CustomUser.objects.get(email=email)

    # generate token
    token = get_random_string(length=32)
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    # Ideally, store token in a model or cache for later verification
    user.encryption_key = token
    user.save()

    subject = "Verify your email address"
    message = f"Hey {user.full_name},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nIf you didn’t create this account, ignore this message."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
