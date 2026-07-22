"""Send automated email reminders to applicants.

Covers:
  * application due  — an application is waiting on the applicant (payment/action)
  * 3 months before expiry
  * 1 month before expiry
  * on the expiry date
  * grace period started (1 day after expiry, 60-day grace)
  * grace reminder (from 2 weeks after expiry) with days left in the grace period

Each reminder is logged so it is only ever sent once per application per stage.
Run daily:  python manage.py send_reminders
Use --dry-run to preview without sending.
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.models import Application, ApplicationStatus
from notifications.emails import notify
from notifications.models import NotificationType, ReminderLog, ReminderStage

GRACE_DAYS = 60

# Statuses where the ball is in the applicant's court.
AWAITING_APPLICANT = {
    ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
    ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
    ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
}
LIVE_CERT_STATUSES = {
    ApplicationStatus.CERTIFICATE_ISSUED,
    ApplicationStatus.RENEWED,
}


class Command(BaseCommand):
    help = 'Send due/expiry/grace-period email reminders to applicants.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry = options['dry_run']
        today = timezone.localdate()
        sent = 0

        def deliver(app, stage, title, message, ntype):
            nonlocal sent
            if ReminderLog.objects.filter(application=app, stage=stage).exists():
                return
            who = app.applicant
            if not who or not who.email:
                return
            self.stdout.write(f'  [{stage}] {app.proposed_street_name} -> {who.email}')
            if not dry:
                notify(who, title, message, notification_type=ntype, application=app)
                ReminderLog.objects.create(application=app, stage=stage)
            sent += 1

        # ---- 1. Application due (awaiting the applicant's payment/action) ----
        for app in Application.objects.filter(status__in=AWAITING_APPLICANT).select_related('applicant'):
            deliver(
                app, ReminderStage.APPLICATION_DUE,
                'Your street naming application is due',
                (f'Dear {app.applicant.first_name or "Applicant"},\n\n'
                 f'Your application for "{app.proposed_street_name}" '
                 f'(Ref: {app.reference_number or app.id}) is awaiting your action — '
                 f'a payment or submission is due before it can proceed.\n\n'
                 f'Please log in to the SNRMS portal to complete it.\n\n'
                 f'Ibeju-Lekki Local Government — Street Naming & Registration.'),
                NotificationType.GENERAL,
            )

        # ---- 2-5. Certificate expiry / grace reminders ----
        live = (Application.objects
                .filter(status__in=LIVE_CERT_STATUSES)
                .exclude(expires_at=None)
                .select_related('applicant'))
        for app in live:
            expiry = app.expires_at
            if isinstance(expiry, datetime.datetime):
                expiry = timezone.localtime(expiry).date()
            days_to_expiry = (expiry - today).days
            name = app.proposed_street_name
            ref = app.reference_number or app.id
            greeting = f'Dear {app.applicant.first_name or "Applicant"},\n\n'
            footer = '\n\nIbeju-Lekki Local Government — Street Naming & Registration.'

            # (i) 3 months before
            if 0 < days_to_expiry <= 92:
                deliver(
                    app, ReminderStage.EXPIRY_3_MONTHS,
                    'Street name registration expires in 3 months',
                    (f'{greeting}The registration of "{name}" (Ref: {ref}) will expire on '
                     f'{expiry:%d %B %Y} — about three months from now. '
                     f'Please plan to renew before that date.{footer}'),
                    NotificationType.RENEWAL_DUE,
                )
            # (ii) 1 month before
            if 0 < days_to_expiry <= 31:
                deliver(
                    app, ReminderStage.EXPIRY_1_MONTH,
                    'Street name registration expires in 1 month',
                    (f'{greeting}The registration of "{name}" (Ref: {ref}) expires on '
                     f'{expiry:%d %B %Y} — one month from now. '
                     f'Please renew to avoid a lapse.{footer}'),
                    NotificationType.RENEWAL_DUE,
                )
            # (iii) on expiry
            if days_to_expiry <= 0:
                deliver(
                    app, ReminderStage.EXPIRY_DUE,
                    'Street name registration has expired today',
                    (f'{greeting}The registration of "{name}" (Ref: {ref}) expired on '
                     f'{expiry:%d %B %Y}. Please renew as soon as possible.{footer}'),
                    NotificationType.RENEWAL_DUE,
                )
            days_past = -days_to_expiry
            grace_end = expiry + datetime.timedelta(days=GRACE_DAYS)
            # (iv) grace period begins — 1 day after expiry
            if days_past >= 1:
                deliver(
                    app, ReminderStage.GRACE_START,
                    f'{GRACE_DAYS}-day grace period has started',
                    (f'{greeting}The registration of "{name}" (Ref: {ref}) expired on '
                     f'{expiry:%d %B %Y}. You are now in a {GRACE_DAYS}-day grace period, '
                     f'which ends on {grace_end:%d %B %Y}. Renew before then to keep the '
                     f'registration active.{footer}'),
                    NotificationType.RENEWAL_DUE,
                )
            # (v) grace reminder — from 2 weeks after expiry, with days remaining
            if days_past >= 14:
                days_left = (grace_end - today).days
                if days_left > 0:
                    deliver(
                        app, ReminderStage.GRACE_REMINDER,
                        f'Grace period reminder — {days_left} days left',
                        (f'{greeting}"{name}" (Ref: {ref}) is still within its grace period, '
                         f'but only {days_left} day(s) remain — the grace period ends on '
                         f'{grace_end:%d %B %Y}. Please renew now to avoid losing the '
                         f'registration.{footer}'),
                        NotificationType.RENEWAL_DUE,
                    )

        prefix = 'Would send' if dry else 'Sent'
        self.stdout.write(self.style.SUCCESS(f'{prefix} {sent} reminder(s).'))
