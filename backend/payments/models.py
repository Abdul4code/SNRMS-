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


def signature_upload_path(instance, filename):
    import os
    return f'official/signature{os.path.splitext(filename)[1]}'


class OfficialSignature(models.Model):
    """The Council Treasurer's e-signature — uploaded ONCE and reused on all receipts.

    Kept server-side and only ever embedded into verified receipts, never exposed
    as a standalone file, so it can't be lifted and reused to forge a receipt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to=signature_upload_path)
    signatory_name = models.CharField(max_length=150, default='Council Treasurer')
    signatory_title = models.CharField(max_length=150, default='Council Treasurer, Ibeju-Lekki LGA')
    uploaded_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL)

    class Meta:
        db_table = 'official_signature'

    @classmethod
    def current(cls):
        return cls.objects.order_by('-uploaded_at').first()


def receipt_upload_path(instance, filename):
    return f'receipts/{instance.serial}.pdf'


class Receipt(models.Model):
    """An issued, tamper-evident payment receipt."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    serial = models.CharField(max_length=40, unique=True, db_index=True)
    payment = models.OneToOneField('payments.Payment', on_delete=models.CASCADE, related_name='receipt')
    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE, related_name='receipts')
    payer_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    stage = models.CharField(max_length=30)
    reference = models.CharField(max_length=100, blank=True)
    security_code = models.CharField(max_length=32, help_text='HMAC digest for anti-forgery verification')
    pdf = models.FileField(upload_to=receipt_upload_path, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'receipts'
        ordering = ['-issued_at']

    def __str__(self):
        return self.serial
