"""Put the streets on the paper register onto the map.

The register — "Names of Registered Streets in Ibeju-Lekki" — is the council's
authority on which names are taken, but it is a list of words: a name, an owner,
a locality, a ward. No coordinates. So it can answer "is this name taken?" and
cannot answer "is the road you just tapped already named?", which is the question
the applicant's map actually asks.

Neither can the survey answer it: of 356 registered streets, only 23 appear
anywhere in the surveyed building records, and OpenStreetMap's geocoder knows
none of them. Most of these names were created by this council and have never
been published anywhere, so no map provider can have them.

Google does know some of them. This asks Google for each one, and — because a
geocoder would rather return something than nothing — throws away everything it
cannot prove:

  * the answer must carry a `route` component whose name shares at least two
    distinctive words with ours (a single shared word is coincidence: "S.D.A
    Church Road" and "Church Street" are not the same street)
  * it must land inside the LGA
  * it must lie within SNAP_M of a road we have imported, and it takes that
    road's line — a point is not a street, and the applicant taps lines

What survives is written to the street's Application and to a Street record, so
the register finally appears on the map: in the validation picker, drawn as a
line, and as the thing that decides whether a tapped road is already named.

    python manage.py geocode_registered_streets --dry-run
    python manage.py geocode_registered_streets
"""
import json
import math
import os
import re
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from applications.localities import canonical_locality
from applications.wards import resolve_ward
from applications.models import Application, ApplicationStatus
from config.models import RoadSegment, Street

GEOCODE = 'https://maps.googleapis.com/maps/api/geocode/json'

# Ibeju-Lekki LGA extent (south, west, north, east).
BBOX = (6.35, 3.60, 6.56, 4.15)

# How close Google's point must be to a road we hold before we believe they are
# the same street.
SNAP_M = 60

# A street registered in Abule Panu does not sit 13 km away in another town. When
# we know where the locality is, an answer outside this radius is the wrong road
# with a similar name, however well the name matched.
LOCALITY_MAX_M = 3000

_REGISTERED = (ApplicationStatus.CERTIFICATE_ISSUED, ApplicationStatus.RENEWED,
               ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED)

# Titles are how a person is addressed, not part of a street's name, and Google
# does not carry them.
_HONORIFIC = (r'^(alhaji|alhaja|alh|chief|hon|dr|prince|princess|engr|mr|mrs|oba|'
              r'sir|pastor|pst|elder|barr|otunba|sheik|rev|gen|brig|prof|late|'
              r'high|bld|sin|capt|arc)\.?\s+')

_TYPE_WORD = (r'\b(street|road|close|avenue|crescent|drive|lane|way|boulevard|'
              r'court|terrace|gardens|grove|place)\b')


def strip_titles(name):
    """"Alh. Prince Ganiyu Eletu Street" -> "Ganiyu Eletu Street"."""
    s = re.sub(r'\s+', ' ', (name or '').strip())
    previous = None
    while previous != s:
        previous = s
        s = re.sub(_HONORIFIC, '', s, flags=re.I)
    return s


def distinctive(name):
    """The words that actually identify a street — no titles, no "Street".

    Initials are joined first: "S.D.A Church Road" must keep SDA, because split
    into "s d a" it is dropped as noise and the street becomes plain "Church",
    which then matches any Church Street in the LGA.
    """
    s = re.sub(_TYPE_WORD, ' ', strip_titles(name), flags=re.I).lower()
    s = re.sub(r'\b([a-z])\.(?=[a-z]\b|[a-z]\.)', r'\1', s)   # s.d.a -> sda
    return {w for w in re.sub(r'[^a-z0-9 ]', ' ', s).split() if len(w) > 2}


def names_agree(ours, theirs):
    """Whether Google's road name is convincingly the one we asked for."""
    want, got = distinctive(ours), distinctive(theirs)
    if not want or not got:
        return False
    shared = want & got
    if len(want) == 1:
        return want == got          # one word is only evidence if it is the whole name
    return len(shared) >= 2 and len(shared) / len(want) >= 0.6


def metres(lat1, lng1, lat2, lng2):
    return math.hypot((lat1 - lat2) * 111000,
                      (lng1 - lng2) * 111000 * math.cos(math.radians(lat1)))


def in_lga(lat, lng):
    s, w, n, e = BBOX
    return s <= lat <= n and w <= lng <= e


class Command(BaseCommand):
    help = "Give the registered streets coordinates, via Google, verified against our roads."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be found; write nothing.')
        parser.add_argument('--cache', default='',
                            help='Read/write Google\'s answers here, so a rerun is free.')
        parser.add_argument('--limit', type=int, default=0,
                            help='Only try this many (for a first look).')
        parser.add_argument('--redo', action='store_true',
                            help='Also try streets that already have coordinates.')

    # --- Google ----------------------------------------------------------
    def ask_google(self, key, name, locality):
        """Google's best answer for this street, or None. Unproven answers are
        discarded here rather than passed on."""
        import requests
        s, w, n, e = BBOX
        clean = strip_titles(name)
        for address in (f'{clean}, {locality}, Ibeju-Lekki, Lagos, Nigeria',
                        f'{clean}, Ibeju-Lekki, Lagos, Nigeria'):
            try:
                r = requests.get(GEOCODE, timeout=30, params={
                    'address': address, 'key': key, 'region': 'ng',
                    'components': 'country:NG', 'bounds': f'{s},{w}|{n},{e}',
                })
                r.raise_for_status()
                data = r.json()
            except Exception as exc:                     # noqa: BLE001
                self.stderr.write(f'  {name}: {exc}')
                return None
            status = data.get('status')
            if status in ('REQUEST_DENIED', 'OVER_QUERY_LIMIT'):
                raise RuntimeError(f'Google refused: {status} — '
                                   f'{data.get("error_message", "")}')
            if status != 'OK':
                continue
            for result in data['results'][:3]:
                loc = result['geometry']['location']
                if not in_lga(loc['lat'], loc['lng']):
                    continue
                roads = [c['long_name'] for c in result.get('address_components', [])
                         if 'route' in c.get('types', [])]
                if roads and names_agree(name, roads[0]):
                    return {'google_name': roads[0],
                            'lat': round(loc['lat'], 7), 'lng': round(loc['lng'], 7)}
        return None

    # --- our own roads ---------------------------------------------------
    def load_centres(self):
        """Where each community is, so an answer can be checked against it."""
        path = os.path.join(settings.BASE_DIR, 'config', 'data',
                            'community_centres.json')
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def load_roads(self):
        roads = []
        for seg in RoadSegment.objects.all().only('id', 'geometry', 'name'):
            try:
                pts = json.loads(seg.geometry)['coordinates']
            except (ValueError, KeyError, TypeError):
                continue
            roads.append((seg, [(p[1], p[0]) for p in pts],
                          (float(seg.min_lat), float(seg.max_lat),
                           float(seg.min_lng), float(seg.max_lng))))
        return roads

    def snap(self, roads, lat, lng):
        """The road this point sits on, and how far off it was."""
        best, best_d = None, float('inf')
        for seg, line, (s_lat, n_lat, w_lng, e_lng) in roads:
            if not (s_lat - 0.01 <= lat <= n_lat + 0.01
                    and w_lng - 0.01 <= lng <= e_lng + 0.01):
                continue
            for plat, plng in line:
                d = metres(lat, lng, plat, plng)
                if d < best_d:
                    best, best_d = seg, d
        return best, best_d

    # --- command ---------------------------------------------------------
    def handle(self, *args, **options):
        key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        cache_path = options['cache']
        cache = {}
        if cache_path and os.path.exists(cache_path):
            try:
                cache = json.load(open(cache_path, encoding='utf-8'))
            except (OSError, ValueError):
                cache = {}
        if not key and not cache:
            self.stderr.write(self.style.ERROR(
                'No GOOGLE_MAPS_API_KEY is set, and no cache to fall back on.'))
            return

        apps = (Application.objects.filter(is_deleted=False, status__in=_REGISTERED)
                .exclude(proposed_street_name='').order_by('reference_number'))
        if not options['redo']:
            apps = apps.filter(latitude__isnull=True)
        apps = list(apps[:options['limit']] if options['limit'] else apps)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'=== Locating {len(apps)} registered streets ==='))
        roads = self.load_roads()
        centres = self.load_centres()
        self.stdout.write(f'  {len(roads)} mapped roads to check against')
        self.stdout.write(f'  {len(centres)} localities with a known centre\n')

        located, unproven, too_far, wrong_place = [], 0, 0, 0
        for i, app in enumerate(apps, 1):
            name = app.proposed_street_name
            full = f'{name} {app.street_type.name}' if app.street_type else name
            locality = app.locality or app.location_description or ''
            ck = f'{full}|{locality}'
            if ck in cache:
                hit = cache[ck]
            else:
                hit = self.ask_google(key, full, locality) if key else None
                cache[ck] = hit
                time.sleep(0.05)          # polite, and well under Google's rate cap
            if not hit:
                unproven += 1
                continue
            centre = centres.get(canonical_locality(locality))
            if centre and metres(hit['lat'], hit['lng'],
                                 centre['lat'], centre['lng']) > LOCALITY_MAX_M:
                wrong_place += 1
                continue
            seg, dist = self.snap(roads, hit['lat'], hit['lng'])
            if seg is None or dist > SNAP_M:
                too_far += 1
                continue
            located.append((app, hit, seg, round(dist)))
            if i % 25 == 0:
                self.stdout.write(f'  …{i}/{len(apps)} — {len(located)} located')

        if cache_path:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=1)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'{len(located)} streets located and '
                                             f'matched to a road on our map.'))
        self.stdout.write(f'  {unproven} Google could not prove (no matching road name)')
        self.stdout.write(f'  {wrong_place} matched the name but in the wrong locality')
        self.stdout.write(f'  {too_far} found, but more than {SNAP_M} m from any road we hold')

        if options['dry_run']:
            for app, hit, seg, dist in located[:40]:
                self.stdout.write(f'    {app.proposed_street_name[:34]:34} -> '
                                  f'"{hit["google_name"]}" {dist} m from road {seg.osm_id}')
            self.stdout.write(self.style.WARNING('\nDry run: nothing was written.'))
            return

        from .build_street_registry import normalize

        written = created = kept = 0
        with transaction.atomic():
            # Codes are unique and sequential; carry on from the highest in use.
            used = [c for c in Street.objects.values_list('code', flat=True)
                    if re.fullmatch(r'IBJ-ST-\d+', c or '')]
            seq = max((int(c.rsplit('-', 1)[1]) for c in used), default=0)

            for app, hit, seg, _dist in located:
                app.latitude, app.longitude = hit['lat'], hit['lng']
                app.save(update_fields=['latitude', 'longitude'])

                # The register only reaches the applicant's map through a Street,
                # so give it one — carrying the road's line, because a street is a
                # line and the applicant taps lines, not points.
                key = normalize(app.proposed_street_name)
                street = Street.objects.filter(normalized_key=key).first()
                if street and street.geometry and not options['redo']:
                    kept += 1          # already has a line; the survey is not overruled
                    continue
                # The register import files the community under location_description,
                # and stamps every row Ward A as a placeholder. Neither is usable:
                # the locality filter needs the community's own name, and the ward
                # follows from it.
                community = canonical_locality(app.locality or app.location_description or '')
                fields = {
                    'name': re.sub(r'\s+', ' ', app.proposed_street_name).strip().title(),
                    'street_type': app.street_type,
                    'ward': resolve_ward(community, hit['lat'], hit['lng']),
                    'locality': community,
                    'latitude': hit['lat'], 'longitude': hit['lng'],
                    'geometry': seg.geometry,
                    'registration_status': Street.RegistrationStatus.REGISTERED,
                    'validation_status': Street.VALIDATION_GOOGLE,
                    'source': Street.SOURCE_DIGITISED,
                }
                if street:
                    for f, v in fields.items():
                        setattr(street, f, v)
                    street.save(update_fields=list(fields))
                    written += 1
                else:
                    seq += 1
                    Street.objects.create(normalized_key=key, code=f'IBJ-ST-{seq:04d}',
                                          building_count=0, name_variants=1, **fields)
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created} streets added to the registry, {written} updated.'))
        if kept:
            self.stdout.write(f'  {kept} left alone — they already have a line from the survey.')
