from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, verify_url):
    subject = "Verify your email"
    message = f"Hello!\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])
    return True
