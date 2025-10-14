from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, verify_url):
    subject = "Verify your email"
    message = f"Hey there 👋\n\nClick the link below to verify your email:\n{verify_url}\n\nIf you didn’t request this, ignore it."
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, message, from_email, [email], fail_silently=False)