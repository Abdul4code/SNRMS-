"""Give every community on the council's list a position on the map.

The applicant picks their locality and the map jumps to it. That only worked for
the couple of dozen communities the field survey happened to cover — the rest had
nowhere to jump to, so they were left out of the picker altogether.

A community's position is taken from the best evidence available:

    survey    the middle of its own surveyed buildings — by far the most reliable
    osm       a named place node in OpenStreetMap
    geocode   OpenStreetMap's geocoder, asked for that community in Ibeju-Lekki

Anything the geocoder puts outside the LGA is thrown away rather than trusted, so
a community that cannot be placed is left without a position instead of being
dropped somewhere wrong.

    python manage.py locate_communities --dry-run
    python manage.py locate_communities
"""
import json
import os
import statistics
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from applications.localities import canonical_locality, official_communities
from config.models import BuildingSurvey

# Ibeju-Lekki LGA extent (south, west, north, east). Anything outside is not here.
BBOX = (6.35, 3.60, 6.56, 4.15)

NOMINATIM = 'https://nominatim.openstreetmap.org/search'
OVERPASS = 'https://overpass-api.de/api/interpreter'
USER_AGENT = ('IbejuLekkiSNRMS/1.0 (community locations; '
              'Ibeju-Lekki Local Government Area)')

OUT_PATH = ('config', 'data', 'community_centres.json')


def in_lga(lat, lng):
    s, w, n, e = BBOX
    return s <= lat <= n and w <= lng <= e


class Command(BaseCommand):
    help = "Work out a map position for every community on the council's list."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be found; write nothing.')
        parser.add_argument('--skip-geocode', action='store_true',
                            help='Use only the survey and OSM places; do not geocode.')

    # --- sources ----------------------------------------------------------
    def from_survey(self):
        """The middle of each community's own surveyed buildings."""
        groups = {}
        for b in BuildingSurvey.objects.exclude(locality='').exclude(latitude=None):
            lat, lng = float(b.latitude), float(b.longitude)
            if not in_lga(lat, lng):
                continue
            groups.setdefault(canonical_locality(b.locality), []).append((lat, lng))
        out = {}
        for name, pts in groups.items():
            out[name] = {
                'lat': round(statistics.median([p[0] for p in pts]), 7),
                'lng': round(statistics.median([p[1] for p in pts]), 7),
                'source': 'survey',
                'buildings': len(pts),
            }
        return out

    def from_osm_places(self, wanted):
        import requests
        s, w, n, e = BBOX
        query = (f'[out:json][timeout:120];'
                 f'(node[place][name]({s},{w},{n},{e});'
                 f' way[place][name]({s},{w},{n},{e});'
                 f' relation[place][name]({s},{w},{n},{e}););out center;')
        try:
            r = requests.post(OVERPASS, data={'data': query}, timeout=180,
                              headers={'User-Agent': USER_AGENT})
            r.raise_for_status()
            elements = r.json()['elements']
        except Exception as exc:                       # noqa: BLE001
            self.stdout.write(self.style.WARNING(f'  OSM places unavailable: {exc}'))
            return {}
        by_name = {}
        for el in elements:
            centre = el if 'lat' in el else el.get('center') or {}
            if 'lat' not in centre:
                continue
            by_name[canonical_locality(el['tags'].get('name', ''))] = centre
        out = {}
        for name in wanted:
            hit = by_name.get(name)
            if hit and in_lga(hit['lat'], hit['lon']):
                out[name] = {'lat': round(hit['lat'], 7), 'lng': round(hit['lon'], 7),
                             'source': 'osm', 'buildings': 0}
        return out

    def geocode(self, name):
        import requests
        try:
            r = requests.get(NOMINATIM, params={
                'q': f'{name}, Ibeju-Lekki, Lagos, Nigeria',
                'format': 'json', 'limit': 1,
                'viewbox': f'{BBOX[1]},{BBOX[2]},{BBOX[3]},{BBOX[0]}', 'bounded': 1,
            }, timeout=30, headers={'User-Agent': USER_AGENT})
            r.raise_for_status()
            hits = r.json()
        except Exception:                               # noqa: BLE001
            return None
        if not hits:
            return None
        lat, lng = float(hits[0]['lat']), float(hits[0]['lon'])
        # The geocoder will happily answer with somewhere in another state.
        return {'lat': round(lat, 7), 'lng': round(lng, 7),
                'source': 'geocode', 'buildings': 0} if in_lga(lat, lng) else None

    # --- command ----------------------------------------------------------
    def handle(self, *args, **options):
        communities = official_communities()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'=== Placing {len(communities)} communities on the map ==='))

        centres = {}
        survey = self.from_survey()
        for name in communities:
            if name in survey:
                centres[name] = survey[name]
        self.stdout.write(f'  from surveyed buildings : {len(centres)}')

        missing = [c for c in communities if c not in centres]
        osm = self.from_osm_places(missing) if missing else {}
        centres.update(osm)
        self.stdout.write(f'  from OSM place names    : {len(osm)}')

        missing = [c for c in communities if c not in centres]
        found = 0
        if missing and not options['skip_geocode']:
            self.stdout.write(f'  geocoding the remaining {len(missing)} '
                              f'(1 per second, as the service asks)…')
            for name in missing:
                hit = self.geocode(name)
                if hit:
                    centres[name] = hit
                    found += 1
                time.sleep(1.1)
        self.stdout.write(f'  from the geocoder       : {found}')

        unplaced = [c for c in communities if c not in centres]
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{len(centres)} of {len(communities)} communities have a position.'))
        if unplaced:
            self.stdout.write(f'still unplaced ({len(unplaced)}): {", ".join(unplaced)}')
            self.stdout.write('  These stay in the picker; the map simply does not jump.')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nDry run: nothing was written.'))
            return
        path = os.path.join(settings.BASE_DIR, *OUT_PATH)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(centres, f, indent=1, sort_keys=True)
        self.stdout.write(f'written: {os.path.join(*OUT_PATH)}')
