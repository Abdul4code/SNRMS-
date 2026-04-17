from django.core.management.base import BaseCommand

from config.models import FeeComponent, FeeConfiguration, StreetType


STREET_TYPES = [
    ('Road',       'RD'),
    ('Street',     'ST'),
    ('Close',      'CL'),
    ('Avenue',     'AVE'),
    ('Crescent',   'CRES'),
    ('Drive',      'DR'),
    ('Lane',       'LN'),
    ('Boulevard',  'BLVD'),
    ('Way',        'WAY'),
    ('Court',      'CT'),
    ('Place',      'PL'),
    ('Terrace',    'TER'),
    ('Gardens',    'GDNS'),
    ('Rise',       'RISE'),
    ('Grove',      'GRV'),
    ('Mews',       'MEWS'),
]

# Street name fee amounts per street type (others default to 30000)
STREET_NAME_FEE_OVERRIDES = {
    'Road':    50000,
    'Street':  40000,
    'Close':   35000,
    'Avenue':  60000,
}

# Flat fee components (component_value, amount)
FLAT_FEES = [
    (FeeComponent.APPLICATION_FEE,          5000),
    (FeeComponent.INSPECTION_FEE,          10000),
    (FeeComponent.RADIO_TV_TAX,             2000),
    (FeeComponent.COMMITTEE_VERIFICATION_FEE, 8000),
    (FeeComponent.SIGNPOST_INSTALLATION_FEE, 25000),
    (FeeComponent.MAP_UPLOAD_FEE,           5000),
    (FeeComponent.RENEWAL_FEE,             20000),
]


class Command(BaseCommand):
    help = 'Seed the database with default street types and fee configurations.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding street types ==='))
        street_type_objects = {}
        created_count = 0
        skipped_count = 0

        for name, code in STREET_TYPES:
            obj, created = StreetType.objects.get_or_create(
                name=name,
                defaults={'code': code},
            )
            street_type_objects[name] = obj
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created street type: {name} ({code})'))
            else:
                skipped_count += 1
                self.stdout.write(f'  Skipped (exists): {name} ({code})')

        self.stdout.write(
            f'Street types — created: {created_count}, skipped: {skipped_count}\n'
        )

        # ------------------------------------------------------------------
        # Flat fee configurations
        # ------------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding flat fee configurations ==='))
        fee_created = 0
        fee_skipped = 0

        for component, amount in FLAT_FEES:
            obj, created = FeeConfiguration.objects.get_or_create(
                component=component,
                street_type=None,
                defaults={'amount': amount},
            )
            if created:
                fee_created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created fee: {component} = {amount}'))
            else:
                fee_skipped += 1
                self.stdout.write(f'  Skipped (exists): {component} = {obj.amount}')

        # ------------------------------------------------------------------
        # Street name fees — one per street type
        # ------------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding street name fees ==='))

        for name, street_type_obj in street_type_objects.items():
            amount = STREET_NAME_FEE_OVERRIDES.get(name, 30000)
            obj, created = FeeConfiguration.objects.get_or_create(
                component=FeeComponent.STREET_NAME_FEE,
                street_type=street_type_obj,
                defaults={'amount': amount},
            )
            if created:
                fee_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Created street_name_fee for {name} = {amount}')
                )
            else:
                fee_skipped += 1
                self.stdout.write(
                    f'  Skipped (exists): street_name_fee for {name} = {obj.amount}'
                )

        self.stdout.write(
            f'Fee configurations — created: {fee_created}, skipped: {fee_skipped}\n'
        )
        self.stdout.write(self.style.SUCCESS('Done. Seed completed successfully.'))
