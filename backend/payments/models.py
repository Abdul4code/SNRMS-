import uuid
from django.db import models
from django.conf import settings


class PaymentStage(models.TextChoices):
    STAGE_A = 'stage_a', 'Stage A - Application Processing'
    STAGE_C = 'stage_c', 'Stage C - Approval & Certificate'
    RENEWAL = 'renewal', 'Renewal'


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SUBMITTED = 'submitted', 'Reference Submitted'
    CONFIRMED = 'confirmed', 'Confirmed by Finance'
    REJECTED = 'rejected', 'Rejected by Finance'


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'applications.Application', on_delete=models.CASCADE,
        related_name='payments'
    )
    stage = models.CharField(max_length=20, choices=PaymentStage.choices)
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    amount_expected = models.DecimalField(max_digits=12, decimal_places=2)
    amount_submitted = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    receipt_file = models.FileField(
        upload_to='payment_receipts/', null=True, blank=True
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='confirmed_payments'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    finance_remarks = models.TextField(blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='submitted_payments'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.stage} payment for {self.application.reference_number}'
