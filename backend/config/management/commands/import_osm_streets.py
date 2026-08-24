"""Give registry streets a real centre-line, taken from OpenStreetMap.

The registry knows where a street's buildings are, not where the street runs, so
the map could only ever show a scatter of dots or a single pin. OSM has the road
centre-lines. This command fetches the named roads across Ibeju-Lekki and attaches
each one's geometry to the registry street it belongs to.

A street is matched on BOTH its name and its position: same normalised name, and
the road passing within MATCH_RADIUS_M of the street's own centroid. Name alone is
not enough — "Church Street" exists in more than one town — so a street with no
coordinates is left alone unless --name-only is passed, and even then only when
exactly one road in the LGA carries that name.

Nothing is invented: a street that finds no confident match keeps its pin, which
is what the map falls back to.

    python manage.py import_osm_streets --dry-run     # report, change nothing
    python manage.py import_osm_streets               # fetch and attach
"""
import json
import math
import re
import time

from django.core.management.base import BaseCommand

from config.models import Street

OVERPASS = 'https://overpass-api.de/api/interpreter'

# Overpass answers 406 to the default python-requests agent, and asks callers to
# say who they are so it can contact whoever is hammering it.
USER_AGENT = ('IbejuLekkiSNRMS/1.0 (street registry import; '
              'Ibeju-Lekki Local Government Area)')

# Ibeju-Lekki LGA extent (south, west, north, east).
BBOX = (6.385, 3.63, 6.520, 4.10)

# Overpass times out on the whole LGA at once; ask for it in tiles.
TILE_LAT, TILE_LNG = 0.07, 0.12

# How far a road may sit from a street's centroid and still be that street.
MATCH_RADIUS_M = 300

TYPE_WORDS = {
    'street', 'road', 'close', 'avenue', 'crescent', 'drive', 'lane', 'way',
    'boulevard', 'court', 'terrace', 'gardens', 'grove', 'mews', 'place',
    'parkway', 'esplanade', 'circus', 'plaza', 'expressway',
}


def normalise(name):
    """Fold a street name so two spellings of it compare equal."""
    s = re.sub(r'[^a-z0-9]+', ' ', (name or '').lower()).strip()
    return re.sub(r'\s+', ' ', s)


def name_key(name):
    """The name without its type word — "Akili Street" and "Akili" are one street."""
    words = [w for w in normalise(name).split() if w not in TYPE_WORDS]
    return ' '.join(words) or normalise(name)


def metres(lat1, lng1, lat2, lng2):
    return math.hypot((lat1 - lat2) * 111000,
                      (lng1 - lng2) * 111000 * math.cos(math.radians(lat1)))


def nearest_point_on(way, lat, lng):
    """Distance in metres from (lat,lng) to the closest vertex of an OSM way."""
    return min(metres(lat, lng, p['lat'], p['lon']) for p in way['geometry'])


class Command(BaseCommand):
    help = 'Attach OpenStreetMap road centre-lines to registry streets.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would match; write nothing.')
        parser.add_argument('--name-only', action='store_true',
                            help='Also match streets that have no coordinates, when '
                                 'exactly one road in the LGA carries that name.')
        parser.add_argument('--radius', type=int, default=MATCH_RADIUS_M,
                            help=f'Match radius in metres (default {MATCH_RADIUS_M}).')
        parser.add_argument('--cache', default='',
                            help='Read/write the fetched OSM data at this path, so a '
                                 'rerun does not hit Overpass again.')

    # --- fetching ---------------------------------------------------------
    def fetch_tile(self, s, w, n, e, attempt=1):
        import requests
        query = f'[out:json][timeout:120];way["highway"]["name"]({s},{w},{n},{e});out geom;'
        try:
            r = requests.post(OVERPASS, data={'data': query}, timeout=180,
                              headers={'User-Agent': USER_AGENT})
            r.raise_for_status()
            return r.json()['elements']
        except Exception as exc:                       # 429 and 504 are routine
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
                    if el['id'] not in seen and el.get('geometry'):
                        seen.add(el['id'])
                        ways.append(el)
                self.stdout.write(f'  tile {lat:.3f},{lng:.3f} -> {len(got)} roads '
                                  f'({len(ways)} so far)')
                lng += TILE_LNG
                time.sleep(3)                          # be a good Overpass citizen
            lat += TILE_LAT

        if cache_path:
            with open(cache_path, 'w') as f:
                json.dump(ways, f)
        return ways

    # --- matching ---------------------------------------------------------
    def handle(self, *args, **options):
        dry = options['dry_run']
        radius = options['radius']
        name_only = options['name_only']

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== Fetching road centre-lines from OpenStreetMap ==='))
        ways = self.fetch_all(options['cache'])
        if not ways:
            self.stdout.write(self.style.ERROR(
                'No roads came back from Overpass — nothing to match. '
                'It rate-limits; try again in a few minutes.'))
            return
        self.stdout.write(f'{len(ways)} named roads in the LGA.')

        # Two indexes: the exact name, and the name with its type word removed so
        # "Akili Street" still finds "Akili". Exact wins, otherwise "Awoyaya Road"
        # and "Awoyaya Street" would both be handed the one road called "Awoyaya".
        by_exact, by_stem = {}, {}
        for way in ways:
            osm_name = way['tags'].get('name', '')
            by_exact.setdefault(normalise(osm_name), []).append(way)
            by_stem.setdefault(name_key(osm_name), []).append(way)

        matched = skipped_far = skipped_noname = matched_by_name = 0
        streets = Street.objects.all()
        for street in streets:
            candidates = (by_exact.get(normalise(street.name))
                          or by_stem.get(name_key(street.name), []))
            if not candidates:
                skipped_noname += 1
                continue

            if street.latitude is not None and street.longitude is not None:
                lat, lng = float(street.latitude), float(street.longitude)
                best, best_d = None, float('inf')
                for way in candidates:
                    d = nearest_point_on(way, lat, lng)
                    if d < best_d:
                        best, best_d = way, d
                if best is None or best_d > radius:
                    skipped_far += 1
                    continue
            elif name_only and len(candidates) == 1:
                # No coordinates at all (the old-register streets). Only safe when
                # the name is unique across the whole LGA.
                best = candidates[0]
                matched_by_name += 1
            else:
                skipped_noname += 1
                continue

            line = {'type': 'LineString',
                    'coordinates': [[p['lon'], p['lat']] for p in best['geometry']]}
            if not dry:
                street.geometry = json.dumps(line)
                if street.latitude is None:
                    mid = best['geometry'][len(best['geometry']) // 2]
                    street.latitude, street.longitude = mid['lat'], mid['lon']
                street.save(update_fields=['geometry', 'latitude', 'longitude'])
            matched += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{"Would attach" if dry else "Attached"} centre-lines to {matched} of '
            f'{streets.count()} streets.'))
        if matched_by_name:
            self.stdout.write(f'  {matched_by_name} matched on a unique name alone '
                              f'(no coordinates to check against).')
        self.stdout.write(f'  {skipped_far} had a name match too far away (>{radius} m) '
                          f'— left with their pin.')
        self.stdout.write(f'  {skipped_noname} had no road of that name — left with their pin.')
        if dry:
            self.stdout.write(self.style.WARNING('Dry run: nothing was written.'))
