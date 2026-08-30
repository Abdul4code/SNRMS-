"""What the council earned, split the way the Chairman thinks about it.

Money is grouped by the kind of work it paid for, not by which fee it was:

    new street   every fee on an application for a name that did not exist
    validation   every fee on an application bringing an existing street onto
                 the register
    renewal      every renewal fee, whichever application it belongs to

That split cannot be read off the payment stage alone, because a validation
application also pays the ordinary application fee — so the stage is combined
with whether the application is a validation.

Each category is also broken down by the fee inside it, so "how much came from
validations" can be followed down to which part of it was the application fee and
which the revalidation fee.
"""
from django.db.models import Count, Sum

from payments.models import Payment, PaymentStage, PaymentStatus

NEW_STREET = 'new_street'
VALIDATION = 'validation'
RENEWAL = 'renewal'

CATEGORIES = (NEW_STREET, VALIDATION, RENEWAL)

CATEGORY_LABELS = {
    NEW_STREET: 'New street names',
    VALIDATION: 'Validations of existing streets',
    RENEWAL: 'Renewals of expired registrations',
}

FEE_LABELS = {
    PaymentStage.STAGE_A: 'Application fee',
    PaymentStage.STAGE_C: 'Certificate fee',
    PaymentStage.REVALIDATION: 'Revalidation fee',
    PaymentStage.RENEWAL: 'Renewal fee',
}


def category_of(payment):
    """Which category a single payment belongs to."""
    if payment.stage == PaymentStage.RENEWAL or payment.application.is_renewal_request:
        return RENEWAL
    return VALIDATION if payment.application.is_legacy else NEW_STREET


def _confirmed(start, end):
    return (Payment.objects
            .filter(status=PaymentStatus.CONFIRMED, confirmed_at__range=(start, end))
            .select_related('application'))


def revenue_breakdown(start, end, category=None):
    """Revenue between two datetimes, by category and by fee within it.

    `category` limits the result to one of CATEGORIES; None returns all three.
    Amounts are what was actually submitted and confirmed, not what was expected.
    """
    wanted = [category] if category in CATEGORIES else list(CATEGORIES)
    buckets = {
        c: {'label': CATEGORY_LABELS[c], 'total': 0.0, 'count': 0, 'fees': {}}
        for c in wanted
    }

    for p in _confirmed(start, end):
        c = category_of(p)
        if c not in buckets:
            continue
        amount = float(p.amount_submitted or 0)
        bucket = buckets[c]
        bucket['total'] += amount
        bucket['count'] += 1
        fee = bucket['fees'].setdefault(
            p.stage, {'label': FEE_LABELS.get(p.stage, p.stage), 'total': 0.0, 'count': 0})
        fee['total'] += amount
        fee['count'] += 1

    return {
        'categories': buckets,
        'total': sum(b['total'] for b in buckets.values()),
        'count': sum(b['count'] for b in buckets.values()),
    }


def applications_in_category(queryset, category):
    """Narrow an Application queryset to one revenue category.

    A renewal is either an application to renew an expired registration, or an
    ordinary application that has since been renewed — so it is matched both by
    the kind of application and by the renewal payments raised against it. That
    also keeps renewals out of the other two categories.
    """
    from django.db.models import Q

    renewals = Q(is_renewal_request=True) | Q(payments__stage=PaymentStage.RENEWAL)
    if category == NEW_STREET:
        return queryset.filter(is_legacy=False).exclude(renewals).distinct()
    if category == VALIDATION:
        return queryset.filter(is_legacy=True).exclude(renewals).distinct()
    if category == RENEWAL:
        return queryset.filter(renewals).distinct()
    return queryset


def revenue_by_stage(start, end):
    """The old stage-only view, kept for anything that still wants it — now
    including revalidation, which used to be left out of the totals entirely."""
    pays = Payment.objects.filter(status=PaymentStatus.CONFIRMED,
                                  confirmed_at__range=(start, end))
    out = {}
    for stage in (PaymentStage.STAGE_A, PaymentStage.STAGE_C,
                  PaymentStage.REVALIDATION, PaymentStage.RENEWAL):
        agg = pays.filter(stage=stage).aggregate(n=Count('id'), total=Sum('amount_submitted'))
        out[stage] = {'label': FEE_LABELS[stage],
                      'count': agg['n'] or 0,
                      'total': float(agg['total'] or 0)}
    return out
