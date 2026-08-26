"""Clear test data so the system can go live, keeping the real LGA records.

Most of what is in the database is NOT test data. The digitised old registry
(legacy applications owned by the import account), the surveyed streets and the
building survey are real and must survive; only the applications and accounts
created while testing are removed.

    python manage.py reset_for_golive --dry-run     # always run this first
    python manage.py reset_for_golive --yes         # actually delete

No staff account is ever deleted. Finance, naming committee, chairman and
superuser accounts always survive — the council's back office has to work the
moment the system opens, and there is no flag to remove them. Only public
applicant accounts are cleared.

Kept: every staff account, street types, fee configuration, fee policy, renewal
settings, the street registry, the building survey, legacy applications and the
import account, and the Treasurer's signature.

Removed: non-legacy applications and everything cascading from them (payments,
receipts, documents, status history, committee reviews, notifications), plus
public applicant accounts left owning nothing and any outstanding verification
codes.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import EmailVerification, User
from applications.models import Application
from audit.models import ActivityLog
from documents.models import Document
from notifications.models import Notification
from payments.models import Payment, Receipt

LEGACY_APPLICANT_EMAIL = 'legacy-registry@ibeju-lekki.gov.ng'
STAFF_ROLES = ('finance', 'naming_committee', 'committee_chairman')


class Command(BaseCommand):
    help = 'Remove test data and leave the database production-ready.'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true',
                            help='Actually delete. Without this the command only reports.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Explicitly report without deleting (the default behaviour).')
        parser.add_argument('--purge-legacy', action='store_true',
                            help='DESTRUCTIVE: also delete the digitised old registry. '
                                 'Only use on a database that has no real imports.')
        parser.add_argument('--reassign-legacy', action='store_true',
                            help='Move legacy applications owned by ordinary users to the '
                                 'import account, so those accounts can be removed too.')
        parser.add_argument('--keep-accounts', action='store_true',
                            help='Keep every account, including public applicants. Their test '
                                 'applications and payments still go; only the logins survive, '
                                 'so testers do not have to register again.')
        parser.add_argument('--delete-media', action='store_true',
                            help='Delete uploaded files belonging to the removed records.')
        parser.add_argument('--apply-fees', action='store_true',
                            help='Finish by applying the official fee schedule '
                                 '(sync_fee_schedule --apply-base).')

    def handle(self, *args, **options):
        write = options['yes'] and not options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('=== Go-live reset ==='))
        if not write:
            self.stdout.write(self.style.WARNING(
                'REPORT ONLY — nothing will be deleted. Re-run with --yes to apply.\n'))

        doomed_apps = Application.objects.all()
        if not options['purge_legacy']:
            doomed_apps = doomed_apps.filter(is_legacy=False)

        kept_legacy = 0 if options['purge_legacy'] else Application.objects.filter(is_legacy=True).count()

        # Collect media paths before the rows go, or we lose the reference.
        media_paths = self._collect_media(doomed_apps) if options['delete_media'] else []

        self._report(doomed_apps, kept_legacy, options)

        if not write:
            self.stdout.write(self.style.WARNING(
                '\nNothing was changed. Re-run with --yes once the numbers above look right.'))
            return

        with transaction.atomic():
            if options['reassign_legacy'] and not options['purge_legacy']:
                self._reassign_legacy()

            app_ids = list(doomed_apps.values_list('id', flat=True))
            # Everything below cascades from Application, but delete the children
            # explicitly so the counts reported are the counts actually removed.
            receipts = Receipt.objects.filter(application_id__in=app_ids).delete()[0]
            payments = Payment.objects.filter(application_id__in=app_ids).delete()[0]
            documents = Document.objects.filter(application_id__in=app_ids).delete()[0]
            apps_deleted = Application.objects.filter(id__in=app_ids).delete()[0]

            # Notifications not tied to an application (account-level notices).
            notes = Notification.objects.filter(application__isnull=True).delete()[0]
            codes = EmailVerification.objects.all().delete()[0]
            logs = ActivityLog.objects.all().delete()[0]

            users_removed = self._delete_users(options)

        self.stdout.write(self.style.SUCCESS(
            f'\nDeleted: {apps_deleted} application rows (incl. cascades), '
            f'{payments} payment rows, {receipts} receipt rows, {documents} document rows, '
            f'{notes} loose notification(s), {codes} verification code(s), '
            f'{logs} activity log row(s), {users_removed} account(s).'))

        if options['delete_media']:
            self._delete_media(media_paths)

        if options['apply_fees']:
            from django.core.management import call_command
            self.stdout.write('')
            call_command('sync_fee_schedule', '--apply-base')

        self._final_state()

    # -- reporting ---------------------------------------------------------

    def _report(self, doomed_apps, kept_legacy, options):
        from config.models import BuildingSurvey, FeeConfiguration, Street, StreetType

        self.stdout.write('  WILL DELETE')
        self.stdout.write(f'    applications (test)      : {doomed_apps.count()}')
        self.stdout.write(f'    payments                 : {Payment.objects.filter(application__in=doomed_apps).count()}')
        self.stdout.write(f'    receipts                 : {Receipt.objects.filter(application__in=doomed_apps).count()}')
        self.stdout.write(f'    documents                : {Document.objects.filter(application__in=doomed_apps).count()}')
        self.stdout.write(f'    verification codes       : {EmailVerification.objects.count()}')
        removable = self._removable_users(options)
        if options.get('keep_accounts'):
            self.stdout.write('    applicant accounts       : 0 (--keep-accounts: every login stays)')
        else:
            self.stdout.write(f'    applicant accounts       : {len(removable)}')
            for u in removable:
                self.stdout.write(f'        {u.email}')
        self.stdout.write('')
        self.stdout.write('  WILL KEEP')
        self.stdout.write(f'    legacy registry apps     : {kept_legacy}')
        self.stdout.write(f'    streets                  : {Street.objects.count()}')
        self.stdout.write(f'    building surveys         : {BuildingSurvey.objects.count()}')
        self.stdout.write(f'    street types             : {StreetType.objects.count()}')
        self.stdout.write(f'    fee rows                 : {FeeConfiguration.objects.count()}')
        kept_users = User.objects.exclude(id__in=[u.id for u in removable])
        label = 'accounts (all)' if options.get('keep_accounts') else 'accounts (all staff)'
        self.stdout.write(f'    {label:24s} : {kept_users.count()}')
        for u in kept_users.order_by('role', 'email'):
            self.stdout.write(f'        {u.email}  ({u.role}{", superuser" if u.is_superuser else ""})')

    # -- users -------------------------------------------------------------

    def _removable_users(self, options):
        """Public applicant accounts only.

        Staff accounts (finance, naming committee, chairman) and superusers are
        never removed — the council's back office has to survive go-live, and
        rebuilding it by hand is how people get locked out of their own system.
        The legacy import account stays too: it owns the digitised registry.
        An applicant still holding an application is also kept, because
        Application.applicant is PROTECTed.
        """
        if options.get('keep_accounts'):
            return []                      # the logins stay; their test data still goes
        removable = []
        for user in User.objects.all():
            if user.is_superuser or user.is_staff:
                continue
            if user.email == LEGACY_APPLICANT_EMAIL:
                continue
            if user.role in STAFF_ROLES:
                continue
            still_owns = Application.objects.filter(applicant=user)
            if not options['purge_legacy']:
                still_owns = still_owns.filter(is_legacy=True)
                if options['reassign_legacy']:
                    still_owns = still_owns.none()
            else:
                still_owns = still_owns.none()
            if still_owns.exists():
                continue
            removable.append(user)
        return removable

    def _reassign_legacy(self):
        owner = User.objects.filter(email=LEGACY_APPLICANT_EMAIL).first()
        if owner is None:
            raise CommandError(
                f'--reassign-legacy needs the import account {LEGACY_APPLICANT_EMAIL}, '
                'which does not exist.')
        moved = Application.objects.filter(is_legacy=True).exclude(applicant=owner).update(applicant=owner)
        if moved:
            self.stdout.write(f'  Reassigned {moved} legacy application(s) to {LEGACY_APPLICANT_EMAIL}.')

    def _delete_users(self, options):
        removed = 0
        for user in self._removable_users(options):
            user.delete()
            removed += 1
        return removed

    # -- media -------------------------------------------------------------

    def _collect_media(self, doomed_apps):
        paths = []
        app_ids = list(doomed_apps.values_list('id', flat=True))
        for qs, field in (
            (Document.objects.filter(application_id__in=app_ids), 'file'),
            (Payment.objects.filter(application_id__in=app_ids), 'receipt_file'),
            (Receipt.objects.filter(application_id__in=app_ids), 'pdf'),
            (doomed_apps, 'certificate_file'),
            (doomed_apps, 'legacy_certificate'),
        ):
            for obj in qs:
                f = getattr(obj, field, None)
                if f:
                    paths.append(f.path if hasattr(f, 'path') else None)
        return [p for p in paths if p]

    def _delete_media(self, paths):
        import os
        gone = 0
        for path in paths:
            try:
                os.remove(path)
                gone += 1
            except OSError:
                pass  # already absent — nothing to reclaim
        self.stdout.write(f'  Removed {gone} uploaded file(s) belonging to deleted records.')

    # -- summary -----------------------------------------------------------

    def _final_state(self):
        from config.models import FeeComponent, FeeConfiguration, StreetType
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Live fee schedule ==='))
        self.stdout.write(f'  {"Street type":<14}{"Base":>14}{"Revalidation":>16}{"Renewal":>13}')
        self.stdout.write(f'  {"-" * 55}')
        for st in StreetType.objects.order_by('name'):
            def amt(component):
                row = FeeConfiguration.objects.filter(
                    component=component, street_type=st, is_active=True).first()
                return row.amount if row else 0
            self.stdout.write(
                f'  {st.name:<14}{amt(FeeComponent.STREET_NAME_FEE):>14,.0f}'
                f'{amt(FeeComponent.REVALIDATION_FEE):>16,.0f}'
                f'{amt(FeeComponent.RENEWAL_FEE):>13,.0f}')
        self.stdout.write(self.style.SUCCESS('\nDatabase is ready for production.'))
