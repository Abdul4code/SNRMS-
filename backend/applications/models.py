import uuid
from django.db import models
from django.conf import settings


class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    AWAITING_STAGE_A_PAYMENT = 'awaiting_stage_a_payment', 'Awaiting Stage A Payment'
    STAGE_A_CONFIRMED = 'stage_a_confirmed', 'Stage A Confirmed'
    UNDER_NAMING_COMMITTEE_REVIEW = 'under_naming_committee_review', 'Under Naming Committee Review'
    APPROVED_BY_COMMITTEE = 'approved_by_committee', 'Approved by Committee'
    REJECTED_BY_COMMITTEE = 'rejected_by_committee', 'Rejected by Committee'
    AWAITING_CHAIRMAN_APPROVAL = 'awaiting_chairman_approval', 'Awaiting Chairman Approval'
    APPROVED_BY_CHAIRMAN = 'approved_by_chairman', 'Approved by Chairman'
    REJECTED_BY_CHAIRMAN = 'rejected_by_chairman', 'Rejected by Chairman'
    AWAITING_STAGE_C_PAYMENT = 'awaiting_stage_c_payment', 'Awaiting Stage C Payment'
    STAGE_C_CONFIRMED = 'stage_c_confirmed', 'Stage C Confirmed'
    CERTIFICATE_ISSUED = 'certificate_issued', 'Certificate Issued'
    EXPIRED = 'expired', 'Expired'
    RENEWAL_SUBMITTED = 'renewal_submitted', 'Renewal Submitted'
    AWAITING_RENEWAL_PAYMENT = 'awaiting_renewal_payment', 'Awaiting Renewal Payment'
    RENEWAL_PAYMENT_CONFIRMED = 'renewal_payment_confirmed', 'Renewal Payment Confirmed'
    RENEWED = 'renewed', 'Renewed'
    WITHDRAWN = 'withdrawn', 'Withdrawn'


VALID_TRANSITIONS = {
    ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.SUBMITTED: [ApplicationStatus.AWAITING_STAGE_A_PAYMENT, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT: [ApplicationStatus.STAGE_A_CONFIRMED],
    ApplicationStatus.STAGE_A_CONFIRMED: [ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW],
    ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW: [
        ApplicationStatus.APPROVED_BY_COMMITTEE,
        ApplicationStatus.REJECTED_BY_COMMITTEE,
    ],
    ApplicationStatus.APPROVED_BY_COMMITTEE: [ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL],
    ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL: [
        ApplicationStatus.APPROVED_BY_CHAIRMAN,
        ApplicationStatus.REJECTED_BY_CHAIRMAN,
    ],
    ApplicationStatus.APPROVED_BY_CHAIRMAN: [ApplicationStatus.AWAITING_STAGE_C_PAYMENT],
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT: [ApplicationStatus.STAGE_C_CONFIRMED],
    ApplicationStatus.STAGE_C_CONFIRMED: [ApplicationStatus.CERTIFICATE_ISSUED],
    ApplicationStatus.CERTIFICATE_ISSUED: [
        ApplicationStatus.EXPIRED,
        ApplicationStatus.RENEWAL_SUBMITTED,
    ],
    ApplicationStatus.EXPIRED: [ApplicationStatus.RENEWAL_SUBMITTED],
    ApplicationStatus.RENEWAL_SUBMITTED: [ApplicationStatus.AWAITING_RENEWAL_PAYMENT],
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT: [ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED],
    ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED: [ApplicationStatus.RENEWED],
    ApplicationStatus.RENEWED: [ApplicationStatus.EXPIRED, ApplicationStatus.RENEWAL_SUBMITTED],
    ApplicationStatus.REJECTED_BY_COMMITTEE: [],
    ApplicationStatus.REJECTED_BY_CHAIRMAN: [],
    ApplicationStatus.WITHDRAWN: [],
}


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=30, unique=True, blank=True)
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='applications'
    )
    proposed_street_name = models.CharField(max_length=200)
    street_type = models.ForeignKey(
        'config.StreetType', on_delete=models.PROTECT,
        related_name='applications'
    )
    location_description = models.TextField()
    lga_area = models.CharField(max_length=200, default='Ibeju-Lekki')
    status = models.CharField(
        max_length=50, choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT
    )
    committee_remarks = models.TextField(blank=True)
    chairman_remarks = models.TextField(blank=True)
    certificate_number = models.CharField(max_length=50, blank=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'applications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reference_number} - {self.proposed_street_name}'

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import datetime
            year = datetime.date.today().year
            count = Application.objects.filter(
                created_at__year=year
            ).count() + 1
            self.reference_number = f'SNR-{year}-{count:05d}'
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status):
        return new_status in VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status, actor=None, remarks=''):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f'Cannot transition from {self.status} to {new_status}'
            )
        old_status = self.status
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])
        StatusHistory.objects.create(
            application=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=actor,
            remarks=remarks,
        )
        return self


class StatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name='status_history'
    )
    from_status = models.CharField(max_length=50)
    to_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'status_history'
        ordering = ['-created_at']
