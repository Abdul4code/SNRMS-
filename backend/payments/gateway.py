"""Paystack payment gateway integration (with a safe demo fallback).

If PAYSTACK_SECRET_KEY is configured, real (test or live) Paystack checkout is
used. If not, the app runs in "demo" mode: the applicant can simulate a
successful payment so the flow can be shown end-to-end without a Paystack
account. Switching to real payments is just adding the keys — no code change.
"""
import hashlib
import hmac
import uuid

import requests
from django.conf import settings
from django.utils import timezone

from accounts.models import Role, User
from applications.models import ApplicationStatus
from .models import Payment, PaymentStage, PaymentStatus
from .services import (
    confirm_renewal_payment,
    confirm_stage_a_payment,
    confirm_stage_c_payment,
)

PAYSTACK_BASE = 'https://api.paystack.co'

# Application state that must precede confirmation, per stage.
_AWAITING = {
    PaymentStage.STAGE_A: (
        ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
        ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION,
    ),
    PaymentStage.STAGE_C: (
        ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
        ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION,
    ),
    PaymentStage.RENEWAL: (
        ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
        ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION,
    ),
}
_CONFIRM = {
    PaymentStage.STAGE_A: confirm_stage_a_payment,
    PaymentStage.STAGE_C: confirm_stage_c_payment,
    PaymentStage.RENEWAL: confirm_renewal_payment,
}


def is_configured() -> bool:
    return bool(getattr(settings, 'PAYSTACK_SECRET_KEY', ''))


def _system_actor() -> User:
    """A non-login system account credited as the confirmer for online payments."""
    user, created = User.objects.get_or_create(
        email='gateway@ibeju-lekki.gov.ng',
        defaults={'first_name': 'Online', 'last_name': 'Payment', 'role': Role.FINANCE, 'is_active': False},
    )
    if created:
        user.set_unusable_password()
        user.save()
    return user


def new_reference(payment: Payment) -> str:
    return f'SNRMS-{payment.stage}-{uuid.uuid4().hex[:12].upper()}'


def initialize(payment: Payment, email: str, callback_url: str) -> dict:
    """Start a Paystack transaction. Returns dict with authorization_url + reference."""
    reference = new_reference(payment)
    payment.payment_reference = reference
    payment.save(update_fields=['payment_reference', 'updated_at'])

    resp = requests.post(
        f'{PAYSTACK_BASE}/transaction/initialize',
        headers={'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'},
        json={
            'email': email,
            'amount': int(float(payment.amount_expected) * 100),  # kobo
            'reference': reference,
            'callback_url': callback_url,
            'metadata': {'payment_id': str(payment.id), 'stage': payment.stage},
        },
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()
    return {
        'authorization_url': body['data']['authorization_url'],
        'reference': reference,
    }


def verify(reference: str) -> dict:
    """Verify a transaction with Paystack. Returns {'success': bool, 'amount': float}."""
    resp = requests.get(
        f'{PAYSTACK_BASE}/transaction/verify/{reference}',
        headers={'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json().get('data', {})
    return {
        'success': data.get('status') == 'success',
        'amount': (data.get('amount') or 0) / 100,
    }


def valid_signature(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature or '')


def mark_paid(payment: Payment, amount: float | None = None) -> Payment:
    """Idempotently move a payment to CONFIRMED and advance the application.

    Mirrors the manual submit→confirm path so the state machine stays valid.
    """
    if payment.status == PaymentStatus.CONFIRMED:
        return payment

    actor = _system_actor()
    now = timezone.now()
    application = payment.application
    awaiting, awaiting_confirm = _AWAITING[payment.stage]

    # Record the submission details.
    payment.status = PaymentStatus.SUBMITTED
    payment.amount_submitted = amount if amount is not None else payment.amount_expected
    payment.payment_date = now.date()
    payment.submitted_by = payment.application.applicant
    payment.submitted_at = now
    payment.save(update_fields=[
        'status', 'amount_submitted', 'payment_date',
        'submitted_by', 'submitted_at', 'updated_at',
    ])

    # Move application into the awaiting-confirmation state if needed.
    if application.status == awaiting:
        application.transition_to(
            awaiting_confirm, actor=actor, remarks='Online payment received.'
        )

    # Confirm and auto-advance.
    _CONFIRM[payment.stage](payment, actor=actor)
    _notify_admins(payment)
    return payment


def _notify_admins(payment: Payment) -> None:
    """Email the Council Treasurer (and other admins) the payment reference."""
    from notifications.emails import notify
    from notifications.models import NotificationType

    app = payment.application
    applicant = app.applicant
    stage_label = payment.get_stage_display() if hasattr(payment, 'get_stage_display') else payment.stage
    title = f'Online payment received — {payment.payment_reference}'
    message = (
        f'An online payment has been confirmed through the payment gateway.\n\n'
        f'Payment reference : {payment.payment_reference}\n'
        f'Amount            : NGN {float(payment.amount_submitted or payment.amount_expected):,.2f}\n'
        f'Stage             : {stage_label}\n'
        f'Street            : {app.proposed_street_name}\n'
        f'Application ref   : {app.reference_number or app.id}\n'
        f'Applicant         : {applicant.first_name} {applicant.last_name} '
        f'<{applicant.email}>\n\n'
        f'The application has been advanced automatically. No manual confirmation is needed.\n\n'
        f'Ibeju-Lekki Local Government — Street Naming & Registration.'
    )
    admins = User.objects.filter(
        role__in=[Role.FINANCE, Role.COMMITTEE_CHAIRMAN, Role.NAMING_COMMITTEE],
        is_active=True,
    ).exclude(email='')
    for admin in admins:
        notify(
            admin, title, message,
            notification_type=NotificationType.PAYMENT_CONFIRMED,
            application=app,
        )
