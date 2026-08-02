import uuid
from django.db import models
from django.conf import settings


class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    AWAITING_STAGE_A_PAYMENT = 'awaiting_stage_a_payment', 'Awaiting Stage A Payment'
    AWAITING_STAGE_A_PAYMENT_CONFIRMATION = 'awaiting_stage_a_payment_confirmation', 'Awaiting Stage A Payment Confirmation'
    STAGE_A_CONFIRMED = 'stage_a_confirmed', 'Stage A Confirmed'
    UNDER_NAMING_COMMITTEE_REVIEW = 'under_naming_committee_review', 'Under Naming Committee Review'
    APPROVED_BY_COMMITTEE = 'approved_by_committee', 'Approved by Committee'
    REJECTED_BY_COMMITTEE = 'rejected_by_committee', 'Rejected by Committee'
    AWAITING_CHAIRMAN_APPROVAL = 'awaiting_chairman_approval', 'Awaiting Chairman Approval'
    APPROVED_BY_CHAIRMAN = 'approved_by_chairman', 'Approved by Chairman'
    REJECTED_BY_CHAIRMAN = 'rejected_by_chairman', 'Rejected by Chairman'
    AWAITING_STAGE_C_PAYMENT = 'awaiting_stage_c_payment', 'Awaiting Stage C Payment'
    AWAITING_STAGE_C_PAYMENT_CONFIRMATION = 'awaiting_stage_c_payment_confirmation', 'Awaiting Stage C Payment Confirmation'
    STAGE_C_CONFIRMED = 'stage_c_confirmed', 'Stage C Confirmed'
    CERTIFICATE_ISSUED = 'certificate_issued', 'Certificate Issued'
    EXPIRED = 'expired', 'Expired'
    RENEWAL_SUBMITTED = 'renewal_submitted', 'Renewal Submitted'
    AWAITING_RENEWAL_PAYMENT = 'awaiting_renewal_payment', 'Awaiting Renewal Payment'
    AWAITING_RENEWAL_PAYMENT_CONFIRMATION = 'awaiting_renewal_payment_confirmation', 'Awaiting Renewal Payment Confirmation'
    RENEWAL_PAYMENT_CONFIRMED = 'renewal_payment_confirmed', 'Renewal Payment Confirmed'
    RENEWED = 'renewed', 'Renewed'
    AWAITING_DOCUMENT_RESUBMISSION = 'awaiting_document_resubmission', 'Awaiting Document Resubmission'
    WITHDRAWN = 'withdrawn', 'Withdrawn'


VALID_TRANSITIONS = {
    ApplicationStatus.DRAFT: [ApplicationStatus.SUBMITTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.SUBMITTED: [ApplicationStatus.AWAITING_STAGE_A_PAYMENT, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT: [ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION],
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION: [
        ApplicationStatus.STAGE_A_CONFIRMED,
        ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
    ],
    ApplicationStatus.STAGE_A_CONFIRMED: [ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW],
    ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW: [
        ApplicationStatus.APPROVED_BY_COMMITTEE,
        ApplicationStatus.REJECTED_BY_COMMITTEE,
        ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION,
    ],
    ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION: [ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW],
    ApplicationStatus.APPROVED_BY_COMMITTEE: [ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL],
    ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL: [
        ApplicationStatus.APPROVED_BY_CHAIRMAN,
        ApplicationStatus.REJECTED_BY_CHAIRMAN,
    ],
    ApplicationStatus.APPROVED_BY_CHAIRMAN: [
        ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
        ApplicationStatus.AWAITING_RENEWAL_PAYMENT,  # legacy applications skip Stage C
    ],
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT: [ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION],
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION: [
        ApplicationStatus.STAGE_C_CONFIRMED,
        ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
    ],
    ApplicationStatus.STAGE_C_CONFIRMED: [ApplicationStatus.CERTIFICATE_ISSUED],
    ApplicationStatus.CERTIFICATE_ISSUED: [
        ApplicationStatus.EXPIRED,
        ApplicationStatus.RENEWAL_SUBMITTED,
    ],
    ApplicationStatus.EXPIRED: [ApplicationStatus.RENEWAL_SUBMITTED],
    ApplicationStatus.RENEWAL_SUBMITTED: [ApplicationStatus.AWAITING_RENEWAL_PAYMENT],
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT: [ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION],
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION: [
        ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
        ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
    ],
    ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED: [ApplicationStatus.RENEWED],
    ApplicationStatus.RENEWED: [ApplicationStatus.EXPIRED, ApplicationStatus.RENEWAL_SUBMITTED],
    ApplicationStatus.REJECTED_BY_COMMITTEE: [],
    ApplicationStatus.REJECTED_BY_CHAIRMAN: [],
    ApplicationStatus.WITHDRAWN: [],
}


class Ward(models.TextChoices):
    WARD_A = 'ward_a', 'Ward A (Ibeju 1)'
    WARD_B = 'ward_b', 'Ward B (Ibeju 2)'
    WARD_C1 = 'ward_c1', 'Ward C1 (Orimedu 1)'
    WARD_C2 = 'ward_c2', 'Ward C2 (Orimedu 2)'
    WARD_D = 'ward_d', 'Ward D (Orimedu 3)'
    WARD_E = 'ward_e', 'Ward E (Iwerekun 1)'
    WARD_F = 'ward_f', 'Ward F (Iwerekun 2)'


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
    ward = models.CharField(max_length=20, choices=Ward.choices, default=Ward.WARD_A)
    lga_area = models.CharField(max_length=200, default='Ibeju-Lekki')
    locality = models.CharField(max_length=200, blank=True, help_text='Town/estate/community — a finer check than ward')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT
    )
    committee_remarks = models.TextField(blank=True)
    chairman_remarks = models.TextField(blank=True)
    signboard_seq = models.PositiveIntegerField(null=True, blank=True, db_index=True,
        help_text='Auto-issued sequence number for signboard/pole; released and recycled on decline')
    signboard_number = models.CharField(max_length=50, blank=True, help_text='Physical signboard number')
    pole_number = models.CharField(max_length=50, blank=True, help_text='Pole number for the street sign')
    is_royalty_exempt = models.BooleanField(default=False, help_text='Chairman-granted: royalty pays only the application fee (Stage C waived)')
    certificate_number = models.CharField(max_length=50, blank=True)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    certificate_released = models.BooleanField(default=False,
        help_text='Whether the applicant may download the certificate. Committee/LG chairman can always download.')
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    is_legacy = models.BooleanField(default=False, help_text='Applicant had a manual certificate before digital registration')
    legacy_certificate = models.FileField(upload_to='legacy_certificates/', null=True, blank=True)
    google_map_uploaded = models.BooleanField(default=False)
    signpost_installed = models.BooleanField(default=False)
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


class CommitteeMember(models.Model):
    """One of the 7 Street Naming Committee members. Member 1 is the chairman.

    All members share the committee login, then verify as a specific member via a
    second-tier PIN. PINs are stored hashed.
    """
    number = models.PositiveSmallIntegerField(unique=True)  # 1..7
    name = models.CharField(max_length=150)
    pin_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'committee_members'
        ordering = ['number']

    @property
    def is_chairman(self):
        return self.number == 1

    def set_pin(self, raw):
        from django.contrib.auth.hashers import make_password
        self.pin_hash = make_password(raw)

    def check_pin(self, raw):
        from django.contrib.auth.hashers import check_password
        return check_password(raw, self.pin_hash)

    def __str__(self):
        return f'Member {self.number} — {self.name}'


class CommitteeMemberComment(models.Model):
    """A committee member's private, signed comment to the LG Chairman.

    Private from other members; visible to the committee chairman and LG Chairman.
    """
    class Recommendation(models.TextChoices):
        RECOMMEND = 'recommend', 'Recommend for approval'
        NOT_RECOMMEND = 'not_recommend', 'Do not recommend'
        ABSTAIN = 'abstain', 'Abstain / neutral'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE,
                                    related_name='committee_comments')
    member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    signature = models.CharField(max_length=150, help_text='Typed signature of the member')
    recommendation = models.CharField(max_length=20, choices=Recommendation.choices,
                                      default=Recommendation.RECOMMEND)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'committee_member_comments'
        unique_together = ('application', 'member')
        ordering = ['member__number']


class CommitteeReview(models.Model):
    """The committee chairman's consolidated output for an application."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField('applications.Application', on_delete=models.CASCADE,
                                       related_name='committee_review')
    general_comment_to_applicant = models.TextField(blank=True)
    overall_recommendation = models.TextField(blank=True)
    decision = models.CharField(max_length=20, default='recommend')
    forwarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'committee_reviews'


class CommitteeSubmissionReview(models.Model):
    """Records that a committee member has viewed an application's submissions (#11)."""
    application = models.ForeignKey('applications.Application', on_delete=models.CASCADE,
                                    related_name='committee_submission_reviews')
    member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'committee_submission_reviews'
        unique_together = ('application', 'member')
