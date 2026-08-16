"""Send an email alongside the in-app notification.

Delivery goes through ``notifications.mailer``, which uses SendGrid in
production and Django's console backend when no provider is configured — so
nothing breaks with no mail account, the message simply appears in the log.
"""
import logging

from . import mailer
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
        mailer.send(title, message, recipient.email)
    return note
