"""
Business logic services for the applications app.

These functions are intentionally kept free of HTTP concerns so they can be
called from views, management commands, Celery tasks, or other services.
"""

import datetime
from decimal import Decimal

from django.utils import timezone

from config.models import FeeComponent, FeeConfiguration
from notifications.models import Notification, NotificationType
from payments.models import Payment, PaymentStage, PaymentStatus

from .models import Application, ApplicationStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_certificate_number() -> str:
    """Return the next CERT-YEAR-NNNNN string."""
    year = timezone.now().year
    count = Application.objects.filter(
        certificate_issued_at__year=year,
        certificate_number__startswith=f'CERT-{year}-',
    ).count() + 1
    return f'CERT-{year}-{count:05d}'


def _stage_a_fee_total(application: Application) -> Decimal:
    """Sum all active Stage A fee components (not street-type-specific)."""
    stage_a_components = [
        FeeComponent.APPLICATION_FEE,
        FeeComponent.INSPECTION_FEE,
        FeeComponent.RADIO_TV_TAX,
        FeeComponent.COMMITTEE_VERIFICATION_FEE,
    ]
    total = FeeConfiguration.objects.filter(
        component__in=stage_a_components,
        is_active=True,
    ).aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('amount')
    )['total'] or Decimal('0.00')
    return total


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def check_street_name_duplicate(name: str, exclude_id=None) -> bool:
    """
    Return True if an active / approved application already uses *name*
    (case-insensitive match on proposed_street_name).

    Excluded statuses are terminal / negative ones that do not represent
    active street-name reservations.
    """
    terminal_statuses = [
        ApplicationStatus.REJECTED_BY_COMMITTEE,
        ApplicationStatus.REJECTED_BY_CHAIRMAN,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.EXPIRED,
    ]
    qs = Application.objects.filter(
        proposed_street_name__iexact=name,
        is_deleted=False,
    ).exclude(status__in=terminal_statuses)

    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)

    return qs.exists()


def submit_application(application: Application, actor) -> Application:
    """
    Transition an application from draft → submitted.

    Raises:
        ValueError: if the application has no uploaded documents.
        ValueError: if the street name is already taken.
        ValueError: if the transition is not valid.
    """
    if not application.is_legacy and not application.documents.filter(is_deleted=False).exists():
        raise ValueError(
            'At least one supporting document must be uploaded before submitting.'
        )

    if check_street_name_duplicate(
        application.proposed_street_name, exclude_id=application.pk
    ):
        raise ValueError(
            f'The proposed street name "{application.proposed_street_name}" is already '
            'in use by another active application.'
        )

    application.transition_to(
        ApplicationStatus.SUBMITTED,
        actor=actor,
        remarks='Application submitted by applicant.',
    )

    notify_applicant(
        application,
        notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
        title='Application Submitted',
        message=(
            f'Your application {application.reference_number} has been submitted '
            'successfully and is awaiting payment processing.'
        ),
    )

    return application


def submit_payment_reference(application: Application, actor) -> Payment:
    """
    Transition submitted → awaiting_stage_a_payment and create a pending
    Stage A Payment record.

    Raises:
        ValueError: if the transition is not valid.
    """
    from django.db.models import Sum as _Sum

    stage_a_components = [
        FeeComponent.APPLICATION_FEE,
        FeeComponent.INSPECTION_FEE,
        FeeComponent.RADIO_TV_TAX,
        FeeComponent.COMMITTEE_VERIFICATION_FEE,
    ]
    total = FeeConfiguration.objects.filter(
        component__in=stage_a_components,
        is_active=True,
    ).aggregate(total=_Sum('amount'))['total'] or Decimal('0.00')

    payment = Payment.objects.create(
        application=application,
        stage=PaymentStage.STAGE_A,
        status=PaymentStatus.PENDING,
        amount_expected=total,
    )

    application.transition_to(
        ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
        actor=actor,
        remarks='Application moved to awaiting Stage A payment.',
    )

    notify_applicant(
        application,
        notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
        title='Payment Required',
        message=(
            f'Your application {application.reference_number} requires Stage A payment '
            f'of ₦{total:,.2f}. Please proceed with payment.'
        ),
    )

    return payment


def advance_to_committee_review(application: Application, actor) -> Application:
    """
    Transition stage_a_confirmed → under_naming_committee_review.

    This is called by the payments app after confirming a Stage A payment.
    """
    application.transition_to(
        ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW,
        actor=actor,
        remarks='Stage A payment confirmed; forwarded to naming committee.',
    )

    notify_applicant(
        application,
        notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
        title='Application Under Review',
        message=(
            f'Your application {application.reference_number} is now under review '
            'by the naming committee.'
        ),
    )

    return application


def issue_certificate(application: Application, actor, expires_at=None) -> Application:
    """
    Generate a certificate number, set issue/expiry dates, and transition
    stage_c_confirmed → certificate_issued.

    Args:
        expires_at: explicit expiry date (datetime.date). Defaults to 5 years from today.

    Raises:
        ValueError: if the transition is not valid.
    """
    cert_number = _next_certificate_number()
    now = timezone.now()
    expires = expires_at if expires_at else (now + datetime.timedelta(days=5 * 365)).date()

    application.certificate_number = cert_number
    application.certificate_issued_at = now
    application.expires_at = expires
    application.save(update_fields=['certificate_number', 'certificate_issued_at', 'expires_at', 'updated_at'])

    application.transition_to(
        ApplicationStatus.CERTIFICATE_ISSUED,
        actor=actor,
        remarks=f'Certificate {cert_number} issued.',
    )

    notify_applicant(
        application,
        notification_type=NotificationType.CERTIFICATE_ISSUED,
        title='Certificate Issued',
        message=(
            f'Your street name certificate ({cert_number}) for application '
            f'{application.reference_number} has been issued. '
            f'It expires on {expires.strftime("%d %B %Y")}.'
        ),
    )

    return application


def notify_applicant(
    application: Application,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    """Create a Notification record for the application's applicant."""
    return Notification.objects.create(
        recipient=application.applicant,
        notification_type=notification_type,
        title=title,
        message=message,
        application=application,
    )
