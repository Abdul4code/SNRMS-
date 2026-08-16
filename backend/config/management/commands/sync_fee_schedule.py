"""Recompute revalidation and renewal fees from the street-name fee schedule.

Both are a percentage of each street type's street-name (Stage C) fee — see
config.FeePolicy — but they are stored as ordinary FeeConfiguration rows so
Finance can still override one street type in the admin UI. This command
rewrites those derived rows from the current policy.

    python manage.py sync_fee_schedule                  # derive from stored base fees
    python manage.py sync_fee_schedule --apply-base     # also reset base fees to the LGA sheet
    python manage.py sync_fee_schedule --dry-run        # show what would change

Pending payments are repriced afterwards so applications already awaiting
payment keep matching the schedule just applied — the same behaviour as
demo_fees / reset_fees.
"""
from django.core.management.base import BaseCommand

from config.models import FeeComponent, FeeConfiguration, FeePolicy, StreetType


class Command(BaseCommand):
    help = 'Recompute revalidation and renewal fees from the street-name fee schedule.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply-base', action='store_true',
            help='Also reset each street-name fee to the official LGA schedule in seed_data.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Print the resulting schedule without writing anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        policy = FeePolicy.get()

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'=== Fee policy: revalidation {policy.revalidation_percent}%, '
            f'renewal {policy.renewal_percent}% of the street-name fee ==='))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be written.\n'))

        if options['apply_base']:
            self._apply_base_schedule(dry_run)

        rows = []
        changed = 0
        for street_type in StreetType.objects.order_by('name'):
            base_cfg = FeeConfiguration.objects.filter(
                component=FeeComponent.STREET_NAME_FEE,
                street_type=street_type, is_active=True,
            ).first()
            if base_cfg is None:
                self.stdout.write(self.style.WARNING(
                    f'  {street_type.name}: no street_name_fee configured — skipped'))
                continue

            base = base_cfg.amount
            derived = {
                FeeComponent.REVALIDATION_FEE: policy.revalidation_fee_for(base),
                FeeComponent.RENEWAL_FEE: policy.renewal_fee_for(base),
            }
            for component, amount in derived.items():
                if not dry_run:
                    obj, created = FeeConfiguration.objects.update_or_create(
                        component=component, street_type=street_type,
                        defaults={'amount': amount, 'is_active': True},
                    )
                    if created or obj.amount != amount:
                        changed += 1
                else:
                    changed += 1

            rows.append((
                street_type.name, base,
                derived[FeeComponent.REVALIDATION_FEE],
                derived[FeeComponent.RENEWAL_FEE],
            ))

        self._print_table(rows)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run — no changes written.'))
            return

        # Retire the old street-type-agnostic renewal row: with per-type renewal
        # fees in place it would otherwise keep shadowing them as a fallback.
        legacy = FeeConfiguration.objects.filter(
            component=FeeComponent.RENEWAL_FEE, street_type__isnull=True, is_active=True)
        if legacy.exists():
            legacy.update(is_active=False)
            self.stdout.write(self.style.WARNING(
                '\nDeactivated the old flat renewal_fee row (now set per street type).'))

        from payments.services import resync_pending_payment_amounts
        repriced = resync_pending_payment_amounts()
        self.stdout.write(self.style.SUCCESS(
            f'\nWrote {len(rows) * 2} derived fee rows; {repriced} pending payment(s) repriced.'))

    def _apply_base_schedule(self, dry_run):
        from .seed_data import DEFAULT_STREET_NAME_FEE, STREET_NAME_FEE_OVERRIDES

        self.stdout.write(self.style.MIGRATE_HEADING('=== Applying base street-name schedule ==='))
        for street_type in StreetType.objects.order_by('name'):
            amount = STREET_NAME_FEE_OVERRIDES.get(street_type.name, DEFAULT_STREET_NAME_FEE)
            existing = FeeConfiguration.objects.filter(
                component=FeeComponent.STREET_NAME_FEE, street_type=street_type).first()
            if existing and existing.amount == amount:
                continue
            was = f'{existing.amount:,.0f}' if existing else 'unset'
            self.stdout.write(f'  {street_type.name}: {was} -> {amount:,}')
            if not dry_run:
                FeeConfiguration.objects.update_or_create(
                    component=FeeComponent.STREET_NAME_FEE, street_type=street_type,
                    defaults={'amount': amount, 'is_active': True},
                )
        self.stdout.write('')

    def _print_table(self, rows):
        if not rows:
            return
        self.stdout.write('')
        self.stdout.write(f'  {"Street type":<14}{"Base":>14}{"Revalidation":>16}{"Renewal":>13}')
        self.stdout.write(f'  {"-" * 55}')
        for name, base, reval, renew in rows:
            self.stdout.write(
                f'  {name:<14}{base:>14,.0f}{reval:>16,.0f}{renew:>13,.0f}')
