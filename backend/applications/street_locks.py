"""Who holds a street while an application for it is being decided.

One street, one applicant at a time — but only for as long as that applicant is
actually moving. The hold runs in two phases:

  * Submitted, nothing paid — a short hold (UNPAID_HOLD_DAYS) so the applicant
    can pay. Let it lapse and the street returns to the pool.
  * Paid — a longer hold (DECISION_HOLD_DAYS) so the committee and the Chairman
    have room to decide. Let that lapse and the street returns to the pool too,
    even though the application carries on.

Once a name is granted the street never returns to the pool.

A street that has come back to the pool can collect several applications. None of
them is auto-rejected: the council sees them ordered by arrival (first, second,
third) and picks. See applications_at_location().

Everything here is derived from the application's own status and its payment
timestamps. Nothing is cached on the row, so a hold cannot drift out of step with
the application it belongs to, and expiry needs no cron job — the hold simply
stops counting the moment it is next read.
"""
import datetime
import math

from django.utils import timezone

from payments.models import PaymentStage, PaymentStatus

from .models import Application, ApplicationStatus

# Two selections within this distance are treated as the same street.
STREET_LOCK_RADIUS_M = 75

# Grace given to an applicant who has not paid yet.
UNPAID_HOLD_DAYS = 3

# Room given to the council to decide once the application fee is in.
DECISION_HOLD_DAYS = 30

# The name is granted or on its way to being issued — the street is gone for good.
SETTLED_STATUSES = frozenset({
    ApplicationStatus.APPROVED_BY_CHAIRMAN,
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION,
    ApplicationStatus.STAGE_C_CONFIRMED,
    ApplicationStatus.CERTIFICATE_ISSUED,
    ApplicationStatus.RENEWAL_SUBMITTED,
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION,
    ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
    ApplicationStatus.RENEWED,
})

# Submitted, no money yet.
UNPAID_STATUSES = frozenset({
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
})

# Fee is in (or at least submitted for confirmation) and a decision is pending.
DECIDING_STATUSES = frozenset({
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION,
    ApplicationStatus.STAGE_A_CONFIRMED,
    ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW,
    ApplicationStatus.APPROVED_BY_COMMITTEE,
    ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL,
    ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION,
})

# Statuses that can hold a street at all — the query filter for candidates.
HOLDING_STATUSES = tuple(SETTLED_STATUSES | UNPAID_STATUSES | DECIDING_STATUSES)


def _stage_a_paid_at(application):
    """When the application fee arrived: confirmation time if Finance has
    confirmed it, otherwise when the applicant submitted the reference."""
    best = None
    for p in application.payments.all():
        if p.stage != PaymentStage.STAGE_A or p.status == PaymentStatus.REJECTED:
            continue
        when = p.confirmed_at or p.submitted_at or p.created_at
        if when and (best is None or when < best):
            best = when
    return best


def lock_state(application, now=None):
    """How this application holds its street right now.

    Returns kind 'settled' (permanent), 'unpaid' or 'decision' (both timed), or
    'none' when the application holds nothing. 'holds' is the answer to the only
    question that matters: may somebody else apply for this street?
    """
    now = now or timezone.now()
    out = {'holds': False, 'kind': 'none', 'expires_at': None, 'seconds_left': None,
           'hold_days': None}
    if application.is_deleted or application.is_legacy:
        return out

    status = application.status
    if status in SETTLED_STATUSES:
        return {**out, 'holds': True, 'kind': 'settled'}

    if status in UNPAID_STATUSES:
        expires = application.created_at + datetime.timedelta(days=UNPAID_HOLD_DAYS)
        kind, days = 'unpaid', UNPAID_HOLD_DAYS
    elif status in DECIDING_STATUSES:
        start = _stage_a_paid_at(application) or application.updated_at
        expires = start + datetime.timedelta(days=DECISION_HOLD_DAYS)
        kind, days = 'decision', DECISION_HOLD_DAYS
    else:
        # Draft, rejected, withdrawn, expired — no claim on the street.
        return out

    return {
        'holds': now < expires,
        'kind': kind,
        'expires_at': expires,
        'seconds_left': max(0, int((expires - now).total_seconds())),
        'hold_days': days,
    }


def _metres(lat1, lng1, lat2, lng2):
    return math.hypot((lat1 - lat2) * 111000,
                      (lng1 - lng2) * 111000 * math.cos(math.radians(lat1)))


def _near(lat, lng, exclude_id=None):
    """Non-legacy applications whose location is the same street as (lat,lng)."""
    qs = (Application.objects
          .filter(is_deleted=False, is_legacy=False)
          .exclude(latitude=None).exclude(longitude=None)
          .prefetch_related('payments'))
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return [a for a in qs
            if _metres(lat, lng, float(a.latitude), float(a.longitude)) <= STREET_LOCK_RADIUS_M]


def street_holder(lat, lng, exclude_id=None, now=None):
    """The application currently holding this street, or None if it is free.

    A hold that has run out is not a hold — the street is open again even though
    the application that used to hold it is still being processed.
    """
    now = now or timezone.now()
    for a in _near(lat, lng, exclude_id):
        if a.status not in HOLDING_STATUSES:
            continue
        if lock_state(a, now)['holds']:
            return a
    return None


def hold_message(application, state):
    """One sentence for the applicant about their own hold."""
    if state['kind'] == 'settled':
        return 'This street is registered to your application.'
    days = max(1, round(state['seconds_left'] / 86400)) if state['seconds_left'] else 0
    if state['kind'] == 'unpaid':
        if not state['holds']:
            return ('The 3 days allowed for payment have passed, so this street is open to '
                    'other applicants again. Pay now to take it back — until someone else '
                    'applies, your application still stands.')
        return (f'This street is held for you, but the application fee must be paid within '
                f'{days} day{"s" if days != 1 else ""}. If it is not, the street opens to '
                f'other applicants again.')
    if not state['holds']:
        return ('The one month allowed for a decision has passed, so this street is open to '
                'other applicants again. Your application is still being processed — if '
                'others apply, the council decides between them.')
    return (f'Your fee is paid, so this street is held for you while the council decides — '
            f'{days} day{"s" if days != 1 else ""} left.')


def applications_at_location(application, now=None):
    """Everyone who has applied for this street, oldest first — so the council can
    see that an application is the second or third for the same location.

    Returns None when the application has no location or nobody else applied.
    """
    if application.latitude is None or application.longitude is None:
        return None
    lat, lng = float(application.latitude), float(application.longitude)
    rivals = _near(lat, lng, exclude_id=application.pk)
    rivals = [a for a in rivals if a.status not in (
        ApplicationStatus.DRAFT, ApplicationStatus.WITHDRAWN)]
    if not rivals:
        return None

    everyone = sorted([application, *rivals], key=lambda a: a.created_at)
    position = next(i for i, a in enumerate(everyone) if a.pk == application.pk) + 1
    return {
        'position': position,
        'total': len(everyone),
        'others': [{
            'id': str(a.pk),
            'reference_number': a.reference_number,
            'applicant_name': getattr(a.applicant, 'full_name', ''),
            'proposed_street_name': a.proposed_street_name,
            'status': a.status,
            'created_at': a.created_at,
            'holds_street': lock_state(a, now)['holds'],
        } for a in everyone if a.pk != application.pk],
    }
