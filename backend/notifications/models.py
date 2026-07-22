import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    APPLICATION_STATUS_CHANGE = 'application_status_change', 'Application Status Change'
    PAYMENT_CONFIRMED = 'payment_confirmed', 'Payment Confirmed'
    PAYMENT_REJECTED = 'payment_rejected', 'Payment Rejected'
    DOCUMENT_VERIFIED = 'document_verified', 'Document Verified'
    CERTIFICATE_ISSUED = 'certificate_issued', 'Certificate Issued'
    APPLICATION_APPROVED = 'application_approved', 'Application Approved'
    APPLICATION_REJECTED = 'application_rejected', 'Application Rejected'
    RENEWAL_DUE = 'renewal_due', 'Renewal Due'
    GENERAL = 'general', 'General'


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=50, choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    application = models.ForeignKey(
        'applications.Application', null=True, blank=True,
        on_delete=models.CASCADE, related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} -> {self.recipient.email}'


class ReminderStage(models.TextChoices):
    APPLICATION_DUE = 'application_due', 'Application payment/action due'
    EXPIRY_3_MONTHS = 'expiry_3_months', '3 months before expiry'
    EXPIRY_1_MONTH = 'expiry_1_month', '1 month before expiry'
    EXPIRY_DUE = 'expiry_due', 'On expiry date'
    GRACE_START = 'grace_start', 'Grace period started (day after expiry)'
    GRACE_REMINDER = 'grace_reminder', 'Grace period reminder (days left)'


class ReminderLog(models.Model):
    """One row per (application, stage) so a reminder is never sent twice."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'applications.Application', on_delete=models.CASCADE, related_name='reminder_logs')
    stage = models.CharField(max_length=32, choices=ReminderStage.choices)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reminder_logs'
        unique_together = ('application', 'stage')
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.stage} -> {self.application_id}'
