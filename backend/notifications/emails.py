"""Send an email alongside the in-app notification.

Uses Django's console backend unless SMTP is configured, so nothing breaks when
no mail account is set up — the message simply appears in the server log.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


def notify(recipient, title, message, notification_type=NotificationType.GENERAL,
           application=None, send_email=True):
    """Create an in-app notification and (optionally) email the recipient."""
    note = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        application=application,
    )
    if send_email and getattr(recipient, 'email', ''):
        try:
            send_mail(
                subject=f'[SNRMS Ibeju-Lekki] {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:  # noqa: BLE001 - email must never break the workflow
            logger.exception('Failed to email %s', recipient.email)
    return note
