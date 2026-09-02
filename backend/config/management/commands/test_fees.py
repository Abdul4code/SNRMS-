"""Put the council's TEST RATES in place so testers can pay real money cheaply.

Stage C is the problem this solves. At the official schedule a Street costs
N500,000 to name, so the pay button reads "Pay N500,016.93 online" and nobody can
put a card through it. These are the rates the LGA issued for testing:

                    new application   revalidation   renewal
    AVENUE                      100            200        80
    ...                         ...            200       ...
    WAY                         195            200       156

Only the three fees that vary by street type are touched. The Stage A fees are
already at test amounts (N124.67 for the four together) and are left alone, as is
the fee policy — so `reset_fees` still restores the official schedule.

    python manage.py test_fees --dry-run
    python manage.py test_fees
    python manage.py reset_fees        # official rates back

Note that `sync_fee_schedule` recomputes revalidation and renewal from the fee
policy's percentages and would overwrite the rates set here; rerun this command
afterwards if that happens.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from config.models import FeeComponent, FeeConfiguration, StreetType

# The council's test sheet, verbatim: street type -> (new application, revalidation, renewal).
TEST_RATES = {
    'Avenue':    (100, 200,  80),
    'Boulevard': (105, 200,  84),
    'Circus':    (110, 200,  88),
    'Close':     (115, 200,  92),
    'Court':     (120, 200,  96),
    'Crescent':  (125, 200, 100),
    'Drive':     (130, 200, 104),
    'Esplanade': (135, 200, 108),
    'Gardens':   (140, 200, 112),
    'Grove':     (145, 200, 116),
    'Lane':      (150, 200, 120),
    'Mews':      (155, 200, 124),
    'Parkway':   (160, 200, 128),
    'Place':     (165, 200, 132),
    'Plaza':     (170, 200, 136),
    'Rise':      (175, 200, 140),
    'Road':      (180, 200, 144),
    'Street':    (185, 200, 148),
    'Terrace':   (190, 200, 152),
    'Way':       (195, 200, 156),
}

# Ibeju Pay's live mode refuses anything under this, and a renewal is a single
# fee paid on its own — so a renewal below it cannot be put through the gateway.
GATEWAY_MINIMUM = Decimal('100')

# Five of the sheet's renewal rates (N80 to N96) are under that minimum, so the
# council added N100 to each to bring them over it. The sheet above is left as
# the council issued it and the lift is applied here, so which rates were changed
# and why stays visible.
SHORTFALL_LIFT = Decimal('100')

# Only fees paid on their own have to clear the minimum. The Stage A components
# are summed into one payment (N124.67 together) and the signpost and map-upload
# fees ride along with Stage C, so none of them is lifted for being small.
STANDALONE_COMPONENTS = (
    FeeComponent.STREET_NAME_FEE,     # dominates Stage C
    FeeComponent.REVALIDATION_FEE,    # the whole revalidation payment
    FeeComponent.RENEWAL_FEE,         # the whole renewal payment
)


class Command(BaseCommand):
    help = "Apply the council's test rates to the per-street-type fees."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would change; write nothing.')

    def handle(self, *args, **options):
        dry = options['dry_run']
        self.stdout.write(self.style.MIGRATE_HEADING('=== Applying the test rates ==='))

        types = {t.name: t for t in StreetType.objects.all()}
        missing = [n for n in TEST_RATES if n not in types]
        if missing:
            self.stdout.write(self.style.WARNING(
                f'  not on the system, skipped: {", ".join(missing)}'))

        # Stage C is the street-name fee plus the two incidentals, so quote the
        # total the applicant will actually be shown on the pay button.
        addons = sum(
            (f.amount for f in FeeConfiguration.objects.filter(
                component__in=(FeeComponent.SIGNPOST_INSTALLATION_FEE,
                               FeeComponent.MAP_UPLOAD_FEE),
                is_active=True)),
            Decimal('0'))

        changed = 0
        lifted = []
        self.stdout.write(f'\n  {"street type":12} {"stage C":>12} {"revalidation":>13} '
                          f'{"renewal":>9}')
        for name, (new_app, reval, renewal) in TEST_RATES.items():
            street_type = types.get(name)
            if street_type is None:
                continue
            row = {}
            for component, sheet_amount in (
                (FeeComponent.STREET_NAME_FEE, new_app),
                (FeeComponent.REVALIDATION_FEE, reval),
                (FeeComponent.RENEWAL_FEE, renewal),
            ):
                amount = Decimal(sheet_amount)
                if component in STANDALONE_COMPONENTS and amount < GATEWAY_MINIMUM:
                    amount += SHORTFALL_LIFT
                    lifted.append((name, component, Decimal(sheet_amount), amount))
                row[component] = amount
                if not dry:
                    FeeConfiguration.objects.update_or_create(
                        component=component, street_type=street_type,
                        defaults={'amount': amount, 'is_active': True},
                    )
                changed += 1
            self.stdout.write(
                f'  {name:12} {row[FeeComponent.STREET_NAME_FEE] + addons:>12} '
                f'{row[FeeComponent.REVALIDATION_FEE]:>13} '
                f'{row[FeeComponent.RENEWAL_FEE]:>9}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{"Would set" if dry else "Set"} {changed} fee rows across '
            f'{len(TEST_RATES) - len(missing)} street types.'))
        self.stdout.write(f'  Stage C shows the rate plus N{addons} of signpost and map fees.')

        if lifted:
            self.stdout.write('')
            self.stdout.write(f'  {len(lifted)} rates were under the gateway\'s '
                              f'N{GATEWAY_MINIMUM:g} minimum, so N{SHORTFALL_LIFT:g} '
                              f'was added to each:')
            for name, component, was, now in lifted:
                self.stdout.write(f'    {name:12} {component:16} N{was:g} -> N{now:g}')
            self.stdout.write('  Every payable stage now clears the minimum.')

        if dry:
            self.stdout.write(self.style.WARNING('\nDry run: nothing was written.'))
            return

        from payments.services import resync_pending_payment_amounts
        n = resync_pending_payment_amounts()
        self.stdout.write(f'  Re-priced {n} pending payment(s) to the test rates.')
