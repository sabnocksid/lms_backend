# accounts/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, verify_url):
    """
    Send email verification link to a newly registered user.
    """
    subject = "Verify your email for LMS"
    message = f"Hello,\n\nPlease verify your email by clicking the link below:\n\n{verify_url}\n\nThank you!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return f"Verification email sent to {email}"
