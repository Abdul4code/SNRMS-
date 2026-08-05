"""Set fees to small random amounts for a low-cost demo, while keeping every
payable stage above the payment gateway's minimum charge (Ibeju Pay live mode
requires at least N100.00 per transaction).

Handy for demoing real online payments in production without charging the real
fees. Run `python manage.py reset_fees` afterwards to restore the official
schedule.

    python manage.py demo_fees            # each stage ~N100-170
    python manage.py demo_fees --min 200  # if the gateway minimum is higher
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from config.models import FeeComponent, FeeConfiguration

# Fees that are summed together into the Stage A payment.
STAGE_A_COMPONENTS = {
    FeeComponent.APPLICATION_FEE,
    FeeComponent.INSPECTION_FEE,
    FeeComponent.RADIO_TV_TAX,
    FeeComponent.COMMITTEE_VERIFICATION_FEE,
}
# Fees that must each clear the minimum on their own (single-fee or dominant-fee stages).
STANDALONE_COMPONENTS = {
    FeeComponent.STREET_NAME_FEE,   # dominates the Stage C payment
    FeeComponent.RENEWAL_FEE,       # the whole Renewal payment
}


class Command(BaseCommand):
    help = ('Set fees to small random demo amounts, keeping every payable stage above the '
            'gateway minimum (default N100).')

    def add_arguments(self, parser):
        parser.add_argument('--min', type=float, default=100.0,
                            help='Gateway minimum charge per transaction, in naira. Default 100.')

    def handle(self, *args, **options):
        gate_min = max(1.0, float(options['min']))
        min_kobo = int(round(gate_min * 100))

        # Stage A is split across 4 fees — each carries a quarter of the minimum plus headroom.
        a_lo = min_kobo // 4 + 200
        a_hi = a_lo + 1500
        # Standalone stages must clear the minimum by themselves.
        big_lo = min_kobo + 100
        big_hi = big_lo + 5000
        # Incidental Stage C add-ons (map upload, signpost) stay tiny.
        small_lo, small_hi = 300, 1000

        def rand_naira(lo, hi):
            return Decimal(random.randint(lo, hi)) / Decimal(100)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'=== Setting demo fees (each payable stage kept above N{gate_min:g}) ==='))
        for fee in FeeConfiguration.objects.select_related('street_type').all():
            if fee.component in STAGE_A_COMPONENTS:
                fee.amount = rand_naira(a_lo, a_hi)
            elif fee.component in STANDALONE_COMPONENTS:
                fee.amount = rand_naira(big_lo, big_hi)
            else:  # map upload, signpost — incidental Stage C add-ons
                fee.amount = rand_naira(small_lo, small_hi)
            fee.is_active = True
            fee.save(update_fields=['amount', 'is_active', 'updated_at'])

        # Report the resulting stage totals so it's obvious they clear the minimum.
        try:
            from payments.services import get_stage_a_fee_breakdown
            stage_a = sum(Decimal(str(x['amount'])) for x in get_stage_a_fee_breakdown())
            self.stdout.write(f'  Stage A total: N{stage_a}')
        except Exception:  # noqa: BLE001
            pass
        renewal = FeeConfiguration.objects.filter(component=FeeComponent.RENEWAL_FEE).first()
        if renewal:
            self.stdout.write(f'  Renewal total: N{renewal.amount}')

        # Re-price outstanding pending payments so they match the new demo fees.
        from payments.services import resync_pending_payment_amounts
        n = resync_pending_payment_amounts()
        self.stdout.write(f'  Re-priced {n} pending payment(s) to the demo amounts.')

        self.stdout.write(self.style.SUCCESS(
            'Demo fees set. Every payable stage is above the gateway minimum. '
            'Run "reset_fees" to restore the official schedule.'))
