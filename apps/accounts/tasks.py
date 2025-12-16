from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_welcome_email(user_email, user_name):
    """
    Simulates sending a welcome email.
    """
    subject = 'Welcome Back to IMDb Clone!'
    message = f'Hi {user_name}, successfully logged into your account.'
    email_from = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@imdb.com'
    
    send_mail(subject, message, email_from, [user_email])
    
    return f"Email sent to {user_email}"