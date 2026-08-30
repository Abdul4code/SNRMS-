"""
Business logic services for the payments app.

These functions are intentionally kept free of HTTP concerns so they can be
called from views, management commands, Celery tasks, or other services.
"""

from django.utils import timezone

from applications.models import ApplicationStatus
from config.models import FeeComponent, FeeConfiguration
from notifications.models import Notification, NotificationType

from .models import Payment, PaymentStage, PaymentStatus


# ---------------------------------------------------------------------------
# Stage A fee components
# ---------------------------------------------------------------------------

_STAGE_A_COMPONENTS = [
    FeeComponent.APPLICATION_FEE,
    FeeComponent.INSPECTION_FEE,
    FeeComponent.RADIO_TV_TAX,
    FeeComponent.COMMITTEE_VERIFICATION_FEE,
]

# Stage C components that do NOT vary by street type
_STAGE_C_FLAT_COMPONENTS = [
    FeeComponent.SIGNPOST_INSTALLATION_FEE,
    FeeComponent.MAP_UPLOAD_FEE,
]


# ---------------------------------------------------------------------------
# Fee breakdown helpers
# ---------------------------------------------------------------------------

def get_stage_a_fee_breakdown() -> list:
    """
    Return a list of {component, label, amount} dicts for all active
    Stage A fee components.
    """
    configs = FeeConfiguration.objects.filter(
        component__in=_STAGE_A_COMPONENTS,
        is_active=True,
    ).order_by('component')

    return [
        {
            'component': cfg.component,
            'label': cfg.get_component_display(),
            'amount': cfg.amount,
        }
        for cfg in configs
    ]


def get_stage_c_fee_breakdown(street_type_id) -> list:
    """
    Return a list of {component, label, amount} dicts for all active
    Stage C fee components.

    street_name_fee is filtered by the given street_type_id; the other
    Stage C components (signpost installation, map upload) are not
    street-type-specific.
    """
    breakdown = []

    # Street-name fee — street-type-specific
    street_name_cfg = FeeConfiguration.objects.filter(
        component=FeeComponent.STREET_NAME_FEE,
        street_type_id=street_type_id,
        is_active=True,
    ).first()
    if street_name_cfg:
        breakdown.append({
            'component': street_name_cfg.component,
            'label': street_name_cfg.get_component_display(),
            'amount': street_name_cfg.amount,
        })

    # Flat Stage C components
    flat_configs = FeeConfiguration.objects.filter(
        component__in=_STAGE_C_FLAT_COMPONENTS,
        is_active=True,
    ).order_by('component')
    for cfg in flat_configs:
        breakdown.append({
            'component': cfg.component,
            'label': cfg.get_component_display(),
            'amount': cfg.amount,
        })

    return breakdown


def get_total_fee(components_list: list):
    """Return the sum of 'amount' values from a fee breakdown list."""
    from decimal import Decimal
    return sum((item['amount'] for item in components_list), Decimal('0.00'))


def _derived_fee(component, street_type_id, percent_getter) -> dict:
    """Return {component, label, amount} for a fee derived from the street-name fee.

    Prefers the stored FeeConfiguration row for this street type, so Finance can
    override an individual type. Falls back to computing the share from the base
    street-name fee, then to the legacy street-type-agnostic row (which is what
    existed before these fees varied per type).
    """
    cfg = None
    if street_type_id:
        cfg = FeeConfiguration.objects.filter(
            component=component, street_type_id=street_type_id, is_active=True,
        ).first()
    if cfg is None and street_type_id:
        base = FeeConfiguration.objects.filter(
            component=FeeComponent.STREET_NAME_FEE,
            street_type_id=street_type_id,
            is_active=True,
        ).first()
        if base is not None:
            from config.models import FeePolicy
            amount = percent_getter(FeePolicy.get(), base.amount)
            return {
                'component': component,
                'label': FeeComponent(component).label,
                'amount': amount,
            }
    if cfg is None:
        cfg = FeeConfiguration.objects.filter(
            component=component, street_type__isnull=True, is_active=True,
        ).first()
    if cfg is None:
        return None
    return {
        'component': cfg.component,
        'label': cfg.get_component_display(),
        'amount': cfg.amount,
    }


def calculate_revalidation_fee(street_type_id=None) -> dict:
    """Revalidation fee for a street type — a share of its street-name fee.

    Charged when an already-named street is brought onto the digital register,
    in place of the full Stage C schedule.
    """
    return _derived_fee(
        FeeComponent.REVALIDATION_FEE, street_type_id,
        lambda policy, base: policy.revalidation_fee_for(base),
    )


def calculate_renewal_fee(street_type_id=None) -> dict:
    """
    Return {component, label, amount} for the renewal fee of a street type.
    Returns None if no renewal fee can be resolved.
    """
    return _derived_fee(
        FeeComponent.RENEWAL_FEE, street_type_id,
        lambda policy, base: policy.renewal_fee_for(base),
    )


def resync_pending_payment_amounts():
    """Recompute amount_expected for every PENDING payment from the current fee
    schedule. Used by the demo_fees / reset_fees commands so payments already
    created keep matching the fees just applied. Returns the number updated."""
    from .models import Payment, PaymentStage, PaymentStatus
    updated = 0
    for p in Payment.objects.filter(status=PaymentStatus.PENDING).select_related('application'):
        if p.stage == PaymentStage.STAGE_A:
            total = get_total_fee(get_stage_a_fee_breakdown())
        elif p.stage == PaymentStage.STAGE_C:
            total = get_total_fee(get_stage_c_fee_breakdown(p.application.street_type_id))
        elif p.stage == PaymentStage.REVALIDATION:
            r = calculate_revalidation_fee(p.application.street_type_id)
            total = r['amount'] if r else None
        elif p.stage == PaymentStage.RENEWAL:
            r = calculate_renewal_fee(p.application.street_type_id)
            total = r['amount'] if r else None
        else:
            total = None
        if total is not None and p.amount_expected != total:
            p.amount_expected = total
            p.save(update_fields=['amount_expected', 'updated_at'])
            updated += 1
    return updated


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------

def _notify_applicant(payment: Payment, notification_type: str, title: str, message: str) -> Notification:
    """Create a Notification record for the payment's application applicant."""
    return Notification.objects.create(
        recipient=payment.application.applicant,
        notification_type=notification_type,
        title=title,
        message=message,
        application=payment.application,
    )


# ---------------------------------------------------------------------------
# Payment confirmation / rejection services
# ---------------------------------------------------------------------------

def confirm_stage_a_payment(payment: Payment, actor) -> Payment:
    """
    Mark the Stage A payment as confirmed, transition the application through
    stage_a_confirmed → under_naming_committee_review, and notify the applicant.
    """
    now = timezone.now()
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_by = actor
    payment.confirmed_at = now
    payment.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])

    application = payment.application

    # stage_a_confirmed
    application.transition_to(
        ApplicationStatus.STAGE_A_CONFIRMED,
        actor=actor,
        remarks='Stage A payment confirmed by finance.',
    )

    # Auto-advance: stage_a_confirmed → under_naming_committee_review
    application.transition_to(
        ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW,
        actor=actor,
        remarks='Stage A payment confirmed; forwarded to naming committee.',
    )

    _notify_applicant(
        payment,
        notification_type=NotificationType.PAYMENT_CONFIRMED,
        title='Stage A Payment Confirmed',
        message=(
            f'Your Stage A payment for application '
            f'{application.reference_number} has been confirmed. '
            'Your application is now under naming committee review.'
        ),
    )

    return payment


def confirm_stage_c_payment(payment: Payment, actor) -> Payment:
    """
    Mark the Stage C payment as confirmed, transition the application to
    stage_c_confirmed, and notify the applicant.
    """
    now = timezone.now()
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_by = actor
    payment.confirmed_at = now
    payment.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])

    application = payment.application

    application.transition_to(
        ApplicationStatus.STAGE_C_CONFIRMED,
        actor=actor,
        remarks='Stage C payment confirmed by finance.',
    )

    _notify_applicant(
        payment,
        notification_type=NotificationType.PAYMENT_CONFIRMED,
        title='Stage C Payment Confirmed',
        message=(
            f'Your Stage C payment for application '
            f'{application.reference_number} has been confirmed. '
            'Your certificate will be issued shortly.'
        ),
    )

    return payment


def confirm_revalidation_payment(payment: Payment, actor) -> Payment:
    """Confirm a revalidation payment for a legacy (already-named) street.

    Shares the renewal machinery — both extend the expiry date and land the
    application in ``renewed`` — but the applicant is told their existing street
    name has been brought onto the register, not that it was renewed.
    """
    return _confirm_term_payment(
        payment, actor, kind='revalidation',
        confirm_remark='Revalidation payment confirmed by finance.',
        renewed_remark='Street name revalidated after payment confirmation.',
        title='Revalidation Payment Confirmed',
        body=(
            'Your revalidation payment for application {ref} has been confirmed. '
            'Your existing street name is now on the digital register and is '
            'valid until {expiry}.'
        ),
    )


def confirm_renewal_payment(payment: Payment, actor) -> Payment:
    """
    Mark the renewal payment as confirmed, transition the application through
    renewal_payment_confirmed → renewed, and notify the applicant.

    A renew-expired *application* is different: its renewal fee is the fee that
    opens the file, and the council has not looked at it yet. That one goes to
    the committee like any other application instead of being renewed on the
    spot — the road is the same as a validation, only the fee differs.
    """
    if payment.application.is_renewal_request:
        return confirm_stage_a_payment(payment, actor)
    return _confirm_term_payment(
        payment, actor, kind='renewal',
        confirm_remark='Renewal payment confirmed by finance.',
        renewed_remark='Application renewed after payment confirmation.',
        title='Renewal Payment Confirmed',
        body=(
            'Your renewal payment for application {ref} has been confirmed. '
            'Your registration has been successfully renewed until {expiry}.'
        ),
    )


def _confirm_term_payment(payment: Payment, actor, kind, confirm_remark,
                          renewed_remark, title, body) -> Payment:
    """Shared body for the revalidation and renewal confirmations."""
    now = timezone.now()
    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_by = actor
    payment.confirmed_at = now
    payment.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])

    application = payment.application

    # Calculate new expiry: extend from current expiry (or today if already past)
    from config.models import RenewalSettings
    import datetime as _dt
    renewal_years = RenewalSettings.get().renewal_years
    base_date = application.expires_at if (application.expires_at and application.expires_at > _dt.date.today()) else _dt.date.today()
    new_expiry = base_date.replace(year=base_date.year + renewal_years)
    application.expires_at = new_expiry
    update_fields = ['expires_at', 'updated_at']
    # For legacy apps, promote the uploaded legacy certificate as the active certificate
    if application.is_legacy and application.legacy_certificate and not application.certificate_file:
        application.certificate_file = application.legacy_certificate
        update_fields.append('certificate_file')
    application.save(update_fields=update_fields)

    # awaiting_renewal_payment_confirmation → renewal_payment_confirmed
    application.transition_to(
        ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
        actor=actor,
        remarks=confirm_remark,
    )

    # Auto-advance: renewal_payment_confirmed → renewed
    application.transition_to(
        ApplicationStatus.RENEWED,
        actor=actor,
        remarks=renewed_remark,
    )

    _notify_applicant(
        payment,
        notification_type=NotificationType.PAYMENT_CONFIRMED,
        title=title,
        message=body.format(
            ref=application.reference_number,
            expiry=new_expiry.strftime('%d %B %Y'),
        ),
    )

    return payment


def reject_payment(payment: Payment, actor, remarks: str = '') -> Payment:
    """
    Mark the payment as rejected, store finance remarks, transition the application
    back to the awaiting-payment state, and notify the applicant.
    """
    now = timezone.now()
    payment.status = PaymentStatus.REJECTED
    payment.confirmed_by = actor
    payment.confirmed_at = now
    payment.finance_remarks = remarks
    payment.save(update_fields=[
        'status', 'confirmed_by', 'confirmed_at', 'finance_remarks', 'updated_at'
    ])

    # Refresh from DB to get the current status (select_related caches the join-time value)
    application = payment.application
    application.refresh_from_db(fields=['status'])

    # Roll the application back so the applicant can re-submit payment evidence
    rejection_remark = f'Payment rejected by finance. {remarks}' if remarks else 'Payment rejected by finance.'
    try:
        if (payment.stage == PaymentStage.STAGE_A and
                application.status == ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION):
            application.transition_to(
                ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
                actor=actor,
                remarks=rejection_remark,
            )
        elif (payment.stage == PaymentStage.STAGE_C and
                application.status == ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION):
            application.transition_to(
                ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
                actor=actor,
                remarks=rejection_remark,
            )
        elif (payment.stage in (PaymentStage.RENEWAL, PaymentStage.REVALIDATION) and
                application.status == ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION):
            application.transition_to(
                ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
                actor=actor,
                remarks=rejection_remark,
            )
    except ValueError:
        pass  # transition not valid — leave status as-is

    _notify_applicant(
        payment,
        notification_type=NotificationType.PAYMENT_REJECTED,
        title='Payment Rejected',
        message=(
            f'Your payment evidence for application {application.reference_number} '
            f'has been rejected by finance. '
            + (f'Reason: {remarks}. ' if remarks else '')
            + 'Please re-submit with the correct details.'
        ),
    )

    return payment
