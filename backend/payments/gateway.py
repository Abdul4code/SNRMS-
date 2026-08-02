"""Ibeju Pay payment gateway integration (with a safe demo fallback).

If IBEJUPAY_SECRET_KEY is configured, real (test or live) Ibeju Pay checkout is
used. If not, the app runs in "demo" mode: the applicant can simulate a
successful payment so the flow can be shown end-to-end without an Ibeju Pay
account. Switching to real payments is just adding the keys — no code change.

API reference: https://ibejupay.com/developers
  POST {base}/transactions/initialize  -> { data: { authorization_url, reference, ... } }
  GET  {base}/transactions/verify/{reference} -> { data: { status, amount, ... } }
  Webhook: header X-IbejuPay-Signature = hex HMAC-SHA512(raw_body, whsec_ secret),
           body { event: "charge.success", data: { reference, amount, status } }
  Amounts are in kobo (naira * 100).
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

def _base_url() -> str:
    return getattr(settings, 'IBEJUPAY_BASE_URL', 'https://ibejupay.com/api/v1').rstrip('/')

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
    return bool(getattr(settings, 'IBEJUPAY_SECRET_KEY', ''))


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
    """Start an Ibeju Pay transaction. Returns dict with authorization_url + reference."""
    reference = new_reference(payment)
    payment.payment_reference = reference
    payment.save(update_fields=['payment_reference', 'updated_at'])

    resp = requests.post(
        f'{_base_url()}/transactions/initialize',
        headers={
            'Authorization': f'Bearer {settings.IBEJUPAY_SECRET_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'email': email,
            'amount': int(round(float(payment.amount_expected) * 100)),  # kobo
            'reference': reference,
            'callback_url': callback_url,
            'metadata': {'payment_id': str(payment.id), 'stage': payment.stage},
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json().get('data', {})
    return {
        'authorization_url': data['authorization_url'],
        'reference': data.get('reference', reference),
    }


def verify(reference: str) -> dict:
    """Verify a transaction with Ibeju Pay. Returns {'success': bool, 'amount': float}.

    The authoritative status/amount live under `data` (data.status == 'success',
    data.amount in kobo); we fall back to top-level fields defensively.
    """
    resp = requests.get(
        f'{_base_url()}/transactions/verify/{reference}',
        headers={'Authorization': f'Bearer {settings.IBEJUPAY_SECRET_KEY}'},
        timeout=20,
    )
    resp.raise_for_status()
    body = resp.json()
    data = body.get('data') or {}
    status_str = data.get('status') or body.get('status')
    amount_kobo = data.get('amount')
    if amount_kobo is None:
        amount_kobo = body.get('amount') or 0
    return {
        'success': status_str == 'success',
        'amount': (amount_kobo or 0) / 100,
    }


def valid_signature(raw_body: bytes, signature: str) -> bool:
    """Verify the X-IbejuPay-Signature header: hex HMAC-SHA512 of the raw body,
    keyed with the webhook signing secret (whsec_...)."""
    secret = getattr(settings, 'IBEJUPAY_WEBHOOK_SECRET', '')
    if not secret:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha512).hexdigest()
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

    # Payment is received but NOT auto-confirmed. The Council Treasurer must
    # confirm it (upon the bank/gateway alert), which then issues the receipt and
    # advances the application. Notify the CT that a payment awaits confirmation.
    _notify_admins(payment)
    return payment


def _notify_admins(payment: Payment) -> None:
    """Email the Council Treasurer (and other admins) the payment reference."""
    from notifications.emails import notify
    from notifications.models import NotificationType

    app = payment.application
    applicant = app.applicant
    stage_label = payment.get_stage_display() if hasattr(payment, 'get_stage_display') else payment.stage
    title = f'Payment awaiting your confirmation — {payment.payment_reference}'
    message = (
        f'An online payment has been received through the payment gateway and is '
        f'awaiting your confirmation.\n\n'
        f'Payment reference : {payment.payment_reference}\n'
        f'Amount            : NGN {float(payment.amount_submitted or payment.amount_expected):,.2f}\n'
        f'Stage             : {stage_label}\n'
        f'Street            : {app.proposed_street_name}\n'
        f'Application ref   : {app.reference_number or app.id}\n'
        f'Applicant         : {applicant.first_name} {applicant.last_name} '
        f'<{applicant.email}>\n\n'
        f'Please review and confirm this payment in your portal to issue the receipt and advance the application.\n\n'
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
