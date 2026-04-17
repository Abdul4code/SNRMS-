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
