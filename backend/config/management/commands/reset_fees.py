"""Restore every fee configuration to the official seed values.

Unlike `seed_data` (which only creates missing rows and skips existing ones),
this OVERWRITES the amounts. Use it to put the official fee schedule back after
lowering fees for a test/demo.

    python manage.py reset_fees
"""
from django.core.management.base import BaseCommand

from config.models import FeeComponent, FeeConfiguration, StreetType
from .seed_data import (
    DEFAULT_STREET_NAME_FEE,
    FLAT_FEES,
    STREET_NAME_FEE_OVERRIDES,
)


class Command(BaseCommand):
    help = 'Restore all fee configurations to the official seed values.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Restoring flat fees ==='))
        for component, amount in FLAT_FEES:
            n = FeeConfiguration.objects.filter(
                component=component, street_type__isnull=True,
            ).update(amount=amount, is_active=True)
            self.stdout.write(f'  {component} -> {amount:,} ({n} row)')

        self.stdout.write(self.style.MIGRATE_HEADING('=== Restoring street name fees ==='))
        for st in StreetType.objects.all().order_by('name'):
            amount = STREET_NAME_FEE_OVERRIDES.get(st.name, DEFAULT_STREET_NAME_FEE)
            n = FeeConfiguration.objects.filter(
                component=FeeComponent.STREET_NAME_FEE, street_type=st,
            ).update(amount=amount, is_active=True)
            self.stdout.write(f'  street_name_fee[{st.name}] -> {amount:,} ({n} row)')

        # Re-price outstanding pending payments back to the official amounts.
        from payments.services import resync_pending_payment_amounts
        n = resync_pending_payment_amounts()
        self.stdout.write(f'Re-priced {n} pending payment(s) to the official amounts.')

        self.stdout.write(self.style.SUCCESS('Fees restored to the official schedule.'))
