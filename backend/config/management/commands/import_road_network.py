"""Import the road network of Ibeju-Lekki from OpenStreetMap, geometry and all.

Not just the named roads — all of them. OSM names barely 5% of the roads here
(228 of 4,510), but it has the shape of nearly all of them, and the shape is the
part the council cannot get anywhere else. The name is ours: it comes from the
applicant or the registry, never from OSM.

This is what lets an applicant point at their street instead of dropping a pin.
Once imported the map snaps locally, with no live call to OSM.

    python manage.py import_road_network --dry-run
    python manage.py import_road_network                  # fetch and store
    python manage.py import_road_network --cache /tmp/roads.json
"""
import json
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from config.models import RoadSegment

OVERPASS = 'https://overpass-api.de/api/interpreter'

# Overpass answers 406 to the default python-requests agent and asks callers to
# identify themselves.
USER_AGENT = ('IbejuLekkiSNRMS/1.0 (street registry road network; '
              'Ibeju-Lekki Local Government Area)')

# Ibeju-Lekki LGA extent (south, west, north, east).
BBOX = (6.385, 3.63, 6.520, 4.10)
TILE_LAT, TILE_LNG = 0.07, 0.12

# Ways that are not streets anyone would apply to name.
SKIP_HIGHWAY = {'motorway', 'motorway_link', 'trunk_link', 'primary_link',
                'secondary_link', 'tertiary_link', 'footway', 'path', 'steps',
                'cycleway', 'bridleway', 'corridor', 'proposed', 'construction'}


class Command(BaseCommand):
    help = 'Import the OpenStreetMap road network so applicants can tap their street.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be imported; write nothing.')
        parser.add_argument('--cache', default='',
                            help='Read/write the fetched roads here, so a rerun does '
                                 'not hit Overpass again.')

    def fetch_tile(self, s, w, n, e, attempt=1):
        import requests
        query = f'[out:json][timeout:120];way["highway"]({s},{w},{n},{e});out geom;'
        try:
            r = requests.post(OVERPASS, data={'data': query}, timeout=240,
                              headers={'User-Agent': USER_AGENT})
            r.raise_for_status()
            return r.json()['elements']
        except Exception as exc:                        # 429 and 504 are routine
            if attempt >= 4:
                self.stdout.write(self.style.WARNING(
                    f'  tile {s:.3f},{w:.3f} gave up after {attempt} tries: {exc}'))
                return []
            wait = 15 * attempt
            self.stdout.write(f'  tile {s:.3f},{w:.3f} retry {attempt} in {wait}s')
            time.sleep(wait)
            return self.fetch_tile(s, w, n, e, attempt + 1)

    def fetch_all(self, cache_path):
        if cache_path:
            try:
                with open(cache_path) as f:
                    ways = json.load(f)
                self.stdout.write(f'Loaded {len(ways)} roads from {cache_path}.')
                return ways
            except (OSError, ValueError):
                pass

        south, west, north, east = BBOX
        ways, seen = [], set()
        lat = south
        while lat < north:
            lng = west
            while lng < east:
                got = self.fetch_tile(lat, lng, min(lat + TILE_LAT, north),
                                      min(lng + TILE_LNG, east))
                for el in got:
                    if el['id'] not in seen and len(el.get('geometry') or []) >= 2:
                        seen.add(el['id'])
                        ways.append(el)
                self.stdout.write(f'  tile {lat:.3f},{lng:.3f} -> {len(got)} roads '
                                  f'({len(ways)} kept)')
                lng += TILE_LNG
                time.sleep(3)
            lat += TILE_LAT

        if cache_path:
            with open(cache_path, 'w') as f:
                json.dump(ways, f)
        return ways

    def handle(self, *args, **options):
        dry = options['dry_run']
        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== Fetching the road network from OpenStreetMap ==='))
        ways = self.fetch_all(options['cache'])
        if not ways:
            self.stdout.write(self.style.ERROR(
                'Nothing came back from Overpass. It rate-limits; try again shortly.'))
            return

        created = updated = skipped = 0
        named = 0
        rows = []
        for way in ways:
            tags = way.get('tags', {})
            pts = way.get('geometry') or []
            # A single point is not a line — guard here rather than only at fetch
            # time, so a cache file cannot smuggle one in.
            if tags.get('highway') in SKIP_HIGHWAY or len(pts) < 2:
                skipped += 1
                continue
            lats = [p['lat'] for p in pts]
            lngs = [p['lon'] for p in pts]
            name = (tags.get('name') or '').strip()
            if name:
                named += 1
            rows.append(dict(
                osm_id=way['id'], name=name[:200], highway=(tags.get('highway') or '')[:40],
                geometry=json.dumps({'type': 'LineString',
                                     'coordinates': [[p['lon'], p['lat']] for p in pts]}),
                min_lat=min(lats), max_lat=max(lats),
                min_lng=min(lngs), max_lng=max(lngs),
            ))

        if not dry:
            with transaction.atomic():
                existing = set(RoadSegment.objects.filter(
                    osm_id__in=[r['osm_id'] for r in rows]).values_list('osm_id', flat=True))
                for row in rows:
                    RoadSegment.objects.update_or_create(osm_id=row['osm_id'], defaults=row)
                    if row['osm_id'] in existing:
                        updated += 1
                    else:
                        created += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{"Would import" if dry else "Imported"} {len(rows)} road segments '
            f'({named} of them named, {len(rows) - named} unnamed but mappable).'))
        if not dry:
            self.stdout.write(f'  {created} new, {updated} refreshed.')
        self.stdout.write(f'  {skipped} skipped (footpaths, slip roads and the like).')
        if dry:
            self.stdout.write(self.style.WARNING('Dry run: nothing was written.'))
