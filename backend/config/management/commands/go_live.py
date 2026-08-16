"""Take the system live in one step.

Runs migrations, clears the test data, applies the official fee schedule and
verifies the result. Everything it does is available as separate commands
(migrate, reset_for_golive, sync_fee_schedule); this is the single entry point
so going live is not a sequence someone can perform half of.

    python manage.py go_live            # report what would happen, change nothing
    python manage.py go_live --yes      # do it

The real LGA records survive: the digitised old registry, the street registry,
the building survey, street types, fee configuration and staff accounts. Only
applications and accounts created while testing are removed. See
reset_for_golive for the full keep/delete breakdown.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Migrate, clear test data, apply the official fee schedule, and verify.'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true',
                            help='Actually make the changes. Without this it only reports.')
        parser.add_argument('--reassign-legacy', action='store_true',
                            help='Move legacy imports owned by ordinary accounts to the import '
                                 'account, so every test account can be removed.')
        parser.add_argument('--keep-media', action='store_true',
                            help='Leave uploaded files on disk instead of deleting the ones '
                                 'belonging to removed records.')

    def handle(self, *args, **options):
        write = options['yes']

        self.stdout.write(self.style.MIGRATE_HEADING(
            '################  SNRMS GO-LIVE  ################'))
        if not write:
            self.stdout.write(self.style.WARNING(
                '\nREPORT ONLY — nothing will be changed.\n'
                'Re-run with --yes once the numbers below look right.\n'
                'Take a database backup first: this is not reversible.\n'))

        # 1. Schema ---------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n[1/3] Applying migrations'))
        if write:
            call_command('migrate', '--noinput', verbosity=0)
            self.stdout.write('  Schema up to date.')
        else:
            call_command('migrate', '--check', '--noinput', verbosity=0)
            self.stdout.write('  Schema already up to date (nothing to apply).')

        # 2. Test data ------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n[2/3] Clearing test data'))
        reset_args = ['reset_for_golive']
        if write:
            reset_args.append('--yes')
            if not options['keep_media']:
                reset_args.append('--delete-media')
        else:
            reset_args.append('--dry-run')
        if options['reassign_legacy']:
            reset_args.append('--reassign-legacy')
        call_command(*reset_args)

        if not write:
            self.stdout.write(self.style.MIGRATE_HEADING('\n[3/3] Fee schedule that would be applied'))
            call_command('sync_fee_schedule', '--apply-base', '--dry-run')
            self.stdout.write(self.style.WARNING(
                '\nNothing was changed. Re-run with --yes to go live.'))
            return

        # 3. Official fees --------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('\n[3/3] Applying the official fee schedule'))
        call_command('sync_fee_schedule', '--apply-base')

        self._verify()

    def _verify(self):
        """Assert the end state is what going live is supposed to mean."""
        from accounts.models import User
        from applications.models import Application
        from config.models import BuildingSurvey, FeeComponent, FeeConfiguration, Street, StreetType
        from payments.models import Payment

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Verification ==='))
        problems = []

        test_apps = Application.objects.filter(is_legacy=False).count()
        if test_apps:
            problems.append(f'{test_apps} non-legacy application(s) still present')
        if Payment.objects.count():
            problems.append(f'{Payment.objects.count()} payment(s) still present')
        if not User.objects.filter(is_superuser=True).exists():
            problems.append('no superuser remains — you would be locked out of the admin')
        if not Street.objects.exists():
            problems.append('street registry is empty — real data may have been lost')
        if not BuildingSurvey.objects.exists():
            problems.append('building survey is empty — real data may have been lost')

        missing = [
            st.name for st in StreetType.objects.all()
            if not FeeConfiguration.objects.filter(
                component=FeeComponent.REVALIDATION_FEE, street_type=st, is_active=True).exists()
        ]
        if missing:
            problems.append(f'no revalidation fee for: {", ".join(missing)}')

        self.stdout.write(f'  legacy registry kept : {Application.objects.filter(is_legacy=True).count()}')
        self.stdout.write(f'  streets kept         : {Street.objects.count()}')
        self.stdout.write(f'  building surveys     : {BuildingSurvey.objects.count()}')
        self.stdout.write(f'  accounts remaining   : {User.objects.count()}')
        for u in User.objects.order_by('role', 'email'):
            self.stdout.write(f'      {u.email}  ({u.role}{", superuser" if u.is_superuser else ""})')

        if problems:
            self.stdout.write('')
            for p in problems:
                self.stdout.write(self.style.ERROR(f'  PROBLEM: {p}'))
            self.stdout.write(self.style.ERROR(
                '\nGo-live finished with problems — review before opening to the public.'))
            return

        self.stdout.write(self.style.SUCCESS(
            '\nAll checks passed. SNRMS is live on the official fee schedule.'))
