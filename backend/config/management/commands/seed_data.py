import csv
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand

from config.models import BuildingSurvey, FeeComponent, FeeConfiguration, StreetType


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

        # ------------------------------------------------------------------
        # Building survey data from CSV
        # ------------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding building survey data ==='))

        csv_path = Path(__file__).resolve().parents[4] / 'Street_Naming_and_Auto_House_Numbering.csv'
        if not csv_path.exists():
            self.stdout.write(self.style.WARNING(f'CSV not found at {csv_path}, skipping survey seed.'))
            return

        def to_bool(val):
            if val in ('yes', '1', 'true'):
                return True
            if val in ('no', '0', 'false'):
                return False
            return None

        def to_int(val):
            try:
                return int(val) if val.strip() else None
            except (ValueError, AttributeError):
                return None

        def to_float(val):
            try:
                return float(val) if val.strip() else None
            except (ValueError, AttributeError):
                return None

        BUILDING_TYPE_MAP = {
            'detached': 'detached',
            'semi_detached': 'semi_detached',
            'flat': 'flat',
            'bungalow': 'bungalow',
            'storey_building': 'storey_building',
        }

        VALID_BUILDING_USE = {'residential', 'commercial', 'mixed', 'institutional', 'other'}
        VALID_OCCUPANCY = {'owner_occupied', 'tenant', 'vacant', 'under_construction'}
        VALID_ACCESS = {'tarred_road', 'untarred_road', 'footpath', 'waterway'}
        VALID_WATER = {'borehole', 'public_tap', 'none'}
        VALID_WASTE = {'regular', 'irregular', 'none'}

        survey_created = 0
        survey_skipped = 0

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                kobo_id = to_int(row.get('_id', ''))
                if kobo_id is None:
                    continue

                raw_uuid = row.get('_uuid', '').strip()
                try:
                    kobo_uuid = uuid.UUID(raw_uuid)
                except ValueError:
                    continue

                # Determine building type from boolean subfields
                building_type = ''
                for bt_key, bt_val in BUILDING_TYPE_MAP.items():
                    if row.get(f'Building_Type/{bt_key}', '0') == '1':
                        building_type = bt_val
                        break
                if not building_type and row.get('Building_Type/others', '0') == '1':
                    building_type = 'others'

                # Determine multi-select fields from boolean subfields
                raw_use = row.get('Building_Use', '').strip().lower()
                building_use = raw_use if raw_use in VALID_BUILDING_USE else ''

                raw_occupancy = row.get('Occupancy_Type', '').strip().lower()
                occupancy_type = raw_occupancy if raw_occupancy in VALID_OCCUPANCY else ''

                raw_access = row.get('Primary_Access_Type', '').strip().lower()
                primary_access_type = raw_access if raw_access in VALID_ACCESS else ''

                raw_water = row.get('Water_Supply', '').strip().lower()
                water_supply = raw_water if raw_water in VALID_WATER else ''

                raw_waste = row.get('Waste_Collection', '').strip().lower()
                waste_collection = raw_waste if raw_waste in VALID_WASTE else ''

                raw_submission = row.get('_submission_time', '').strip()
                submission_time = None
                if raw_submission:
                    from django.utils.dateparse import parse_datetime
                    from django.utils.timezone import make_aware
                    dt = parse_datetime(raw_submission)
                    if dt is not None:
                        submission_time = dt if dt.tzinfo else make_aware(dt)

                raw_date = row.get('date', '').strip()
                survey_date = None
                if raw_date:
                    from django.utils.dateparse import parse_date
                    survey_date = parse_date(raw_date)

                _, created = BuildingSurvey.objects.get_or_create(
                    kobo_id=kobo_id,
                    defaults=dict(
                        kobo_uuid=kobo_uuid,
                        submission_time=submission_time,
                        enumerator_id=row.get('Enumerator_ID', '').strip(),
                        survey_date=survey_date,
                        locality=row.get('Locality', '').strip(),
                        ward=row.get('Ward', '').strip(),
                        latitude=to_float(row.get('_location_latitude', '')),
                        longitude=to_float(row.get('_location_longitude', '')),
                        existing_street_name=row.get('Street_Name_if_any', '').strip(),
                        proposed_street_name=row.get('Proposed_Street_Name', '').strip(),
                        existing_house_number=row.get('House_Building_Number_if_any', '').strip(),
                        proposed_auto_number=row.get('Proposed_Auto_Number', '').strip(),
                        building_use=building_use,
                        building_type=building_type,
                        building_type_other=row.get('Others_001', '').strip(),
                        number_of_floors=to_int(row.get('Number_of_Floors', '')),
                        number_of_flats=to_int(row.get('Number_of_Flats', '')),
                        number_of_shops=to_int(row.get('Number_of_Shops', '')),
                        compound_fence=to_bool(row.get('Compound_Fence', '').strip().lower()),
                        occupancy_type=occupancy_type,
                        primary_access_type=primary_access_type,
                        vehicle_accessible=to_bool(row.get('Is_the_building_accessible_by_vehicle', '').strip().lower()),
                        electricity_connection=to_bool(row.get('Electricity_Connection', '').strip().lower()),
                        water_supply=water_supply,
                        waste_collection=waste_collection,
                        nearby_landmark=row.get('Nearby_Landmark', '').strip(),
                        land_title_type=row.get('Land_Tile_Type', '').strip(),
                        owner_name=row.get('Owner_Name_if_available', '').strip(),
                        contact_number=row.get('Contact_Number_Optional', '').strip(),
                        land_size=row.get('Size_of_land_optional', '').strip(),
                        photo_url=row.get('Captured_Photo_of_Building_Frontage_URL', '').strip(),
                    ),
                )
                if created:
                    survey_created += 1
                else:
                    survey_skipped += 1

        self.stdout.write(
            f'Building surveys — created: {survey_created}, skipped: {survey_skipped}\n'
        )
        self.stdout.write(self.style.SUCCESS('Done. All seeds completed successfully.'))
