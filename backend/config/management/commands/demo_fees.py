"""Set every fee to a small random amount (below N20) for a low-cost demo.

Handy for demoing real online payments in production without charging the real
fees. Run `python manage.py reset_fees` afterwards to restore the official
schedule.

    python manage.py demo_fees            # random amounts N1.00–N19.99
    python manage.py demo_fees --max 5    # random amounts up to N5.00
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from config.models import FeeConfiguration


class Command(BaseCommand):
    help = 'Set every fee to a small random amount (below the given max, default N20) for demos.'

    def add_arguments(self, parser):
        parser.add_argument('--max', type=float, default=20.0,
                            help='Upper bound in naira (exclusive). Default 20.')

    def handle(self, *args, **options):
        ceiling = max(1.0, float(options['max']))
        # Random kobo amount in [100, ceiling*100 - 1] -> N1.00 .. just under the max.
        top = max(100, int(ceiling * 100) - 1)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'=== Setting all fees to random amounts below N{ceiling:g} (demo) ==='))
        count = 0
        for fee in FeeConfiguration.objects.select_related('street_type').all():
            fee.amount = Decimal(random.randint(100, top)) / Decimal(100)
            fee.is_active = True
            fee.save(update_fields=['amount', 'is_active', 'updated_at'])
            label = fee.component
            if fee.street_type:
                label += f'[{fee.street_type.name}]'
            self.stdout.write(f'  {label} -> N{fee.amount}')
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{count} fees set to random demo amounts. Run "reset_fees" to restore the official schedule.'))
