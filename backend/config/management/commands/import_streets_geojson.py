"""Import a properly digitised street network (ground-truth) from GeoJSON.

Expects a GeoJSON FeatureCollection of LineString (or MultiLineString) features —
the kind QGIS exports. Each feature becomes an authoritative Street record with
real geometry, replacing the auto-derived (survey-clustered) streets.

Recognised feature properties (all optional except that a name is recommended):
    name        -> street name (leave blank for an unnamed street to be named later)
    street_type -> e.g. "Road", "Close" (matched to the StreetType table)
    ward, locality
    code        -> your own street code; auto-assigned (IBJ-ST-NNNN) if absent

Usage:
    python manage.py import_streets_geojson streets.geojson            # add digitised streets
    python manage.py import_streets_geojson streets.geojson --replace  # first delete auto streets
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from config.models import Street, StreetType, BuildingSurvey


def _line_midpoint(coords):
    """Rough centroid of a LineString for map labelling (coords are [lng, lat])."""
    if not coords:
        return None, None
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


class Command(BaseCommand):
    help = 'Import a digitised street network (GeoJSON) as the ground-truth Street layer.'

    def add_arguments(self, parser):
        parser.add_argument('geojson_path')
        parser.add_argument('--replace', action='store_true',
                            help='Delete existing auto (survey-derived) streets first.')

    @transaction.atomic
    def handle(self, *args, **options):
        path = options['geojson_path']
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Could not read GeoJSON: {exc}')

        features = data.get('features', []) if isinstance(data, dict) else []
        if not features:
            raise CommandError('No features found in the GeoJSON FeatureCollection.')

        if options['replace']:
            # Detach buildings, remove the auto layer; digitised streets take over.
            BuildingSurvey.objects.update(street=None)
            removed = Street.objects.filter(source=Street.SOURCE_SURVEY).delete()[0]
            self.stdout.write(f'Removed {removed} auto (survey-derived) streets.')

        street_types = {st.name.lower(): st for st in StreetType.objects.all()}
        # Continue codes after the current maximum.
        last = Street.objects.order_by('-code').values_list('code', flat=True).first()
        seq = 0
        if last and last.startswith('IBJ-ST-'):
            try:
                seq = int(last.rsplit('-', 1)[1])
            except ValueError:
                seq = Street.objects.count()

        created = skipped = 0
        for feat in features:
            geom = (feat or {}).get('geometry') or {}
            gtype = geom.get('type')
            props = feat.get('properties', {}) or {}
            if gtype == 'LineString':
                coords = geom.get('coordinates', [])
            elif gtype == 'MultiLineString':
                coords = [pt for part in geom.get('coordinates', []) for pt in part]
            else:
                skipped += 1
                continue
            if len(coords) < 2:
                skipped += 1
                continue

            name = (props.get('name') or props.get('Name') or props.get('street_name') or '').strip()
            st = street_types.get(str(props.get('street_type', '')).strip().lower())
            lat, lng = _line_midpoint(coords)
            seq += 1
            code = str(props.get('code') or f'IBJ-ST-{seq:04d}').strip()
            key = (name.lower() or code.lower())
            # Keep normalized_key unique.
            base, i = key, 2
            while Street.objects.filter(normalized_key=key).exists():
                key = f'{base} {i}'; i += 1

            Street.objects.create(
                name=name.title() if name else f'Unnamed street {code}',
                normalized_key=key,
                code=code,
                street_type=st,
                ward=str(props.get('ward', '')).strip(),
                locality=str(props.get('locality', '')).strip(),
                latitude=lat, longitude=lng,
                geometry=json.dumps({'type': 'LineString', 'coordinates': coords}),
                source=Street.SOURCE_DIGITISED,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Digitised streets imported — created: {created}, skipped: {skipped}. '
            f'Next: run "attach_names_from_points" to transfer survey names onto these streets.'
        ))
