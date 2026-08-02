"""Duplicate street-name detection.

Checks a proposed street name against the canonical Street registry and against
already-registered applications, by name (globally and within a locality) and by
geographic proximity — so applicants can't propose a name that already exists.
"""
import math
import re

from config.models import Street
from .models import Application, ApplicationStatus

_TYPE_FIX = {
    'streeet': 'street', 'stret': 'street', 'str': 'street', 'st': 'street',
    'rd': 'road', 'ave': 'avenue', 'av': 'avenue', 'cres': 'crescent', 'cr': 'crescent',
    'cl': 'close', 'dr': 'drive', 'ln': 'lane', 'blvd': 'boulevard', 'ct': 'court',
}
_REGISTERED_STATUSES = {
    ApplicationStatus.CERTIFICATE_ISSUED,
    ApplicationStatus.RENEWED,
    ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
}
NEARBY_METERS = 300


def normalize(raw: str) -> str:
    s = (raw or '').strip().lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return ' '.join(_TYPE_FIX.get(t, t) for t in s.split())


def _haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def check_duplicate(name, locality=None, latitude=None, longitude=None):
    """Return a structured duplicate report for a proposed street name."""
    key = normalize(name)
    loc_norm = (locality or '').strip().lower()
    try:
        lat = float(latitude) if latitude not in (None, '') else None
        lng = float(longitude) if longitude not in (None, '') else None
    except (TypeError, ValueError):
        lat = lng = None

    name_matches = []          # same name anywhere
    locality_matches = []      # same name in the same locality
    nearby = []                # named streets close to the proposed point

    # 1) Canonical registry matches by normalized name.
    for st in Street.objects.filter(normalized_key=key):
        dist = None
        if lat is not None and st.latitude is not None:
            dist = round(_haversine_m(lat, lng, float(st.latitude), float(st.longitude)))
        entry = {
            'source': 'registry', 'code': st.code, 'name': st.name,
            'locality': st.locality, 'ward': st.ward,
            'registration_status': st.registration_status,
            'distance_m': dist,
        }
        name_matches.append(entry)
        if loc_norm and st.locality and loc_norm in st.locality.lower():
            locality_matches.append(entry)

    # 2) Registered application names (covers streets not in the survey).
    for a in Application.objects.filter(status__in=_REGISTERED_STATUSES):
        full = normalize(f'{a.proposed_street_name} {a.street_type.name if a.street_type else ""}')
        if normalize(a.proposed_street_name) == key or full == key:
            entry = {
                'source': 'registered', 'code': a.reference_number,
                'name': a.proposed_street_name, 'locality': a.locality or '',
                'ward': a.get_ward_display(), 'registration_status': 'registered',
                'distance_m': None,
            }
            name_matches.append(entry)
            if loc_norm and a.locality and loc_norm in a.locality.lower():
                locality_matches.append(entry)

    # 3) Proximity: named streets near the proposed point (context + strong signal).
    if lat is not None:
        for st in Street.objects.exclude(latitude=None):
            d = _haversine_m(lat, lng, float(st.latitude), float(st.longitude))
            if d <= NEARBY_METERS:
                nearby.append({
                    'code': st.code, 'name': st.name, 'locality': st.locality,
                    'distance_m': round(d), 'same_name': st.normalized_key == key,
                })
        nearby.sort(key=lambda x: x['distance_m'])

    # Verdict.
    if name_matches and (locality_matches or any(n['same_name'] for n in nearby) or not loc_norm):
        verdict = 'duplicate'
    elif name_matches:
        verdict = 'possible'      # same name exists, but a different locality
    else:
        verdict = 'clear'

    # "Cannot rename until the previous name expires" — a street with an active
    # (unexpired) registration cannot be renamed until its registration lapses.
    from django.utils import timezone
    import datetime as _dt
    now = timezone.now()
    rename_blocked = None
    RENAME_METERS = 60
    for a in Application.objects.filter(status__in=_REGISTERED_STATUSES).exclude(expires_at=None):
        exp = a.expires_at
        if isinstance(exp, _dt.datetime):
            exp_dt = exp if timezone.is_aware(exp) else timezone.make_aware(exp)
        else:  # a plain date
            exp_dt = timezone.make_aware(_dt.datetime.combine(exp, _dt.time.max))
        if exp_dt <= now:
            continue  # already expired — a new name is allowed
        same_name = normalize(a.proposed_street_name) == key
        close = False
        if lat is not None and a.latitude is not None:
            close = _haversine_m(lat, lng, float(a.latitude), float(a.longitude)) <= RENAME_METERS
        if same_name or close:
            rename_blocked = {
                'name': a.proposed_street_name,
                'reference': a.reference_number,
                'expires_at': a.expires_at,
            }
            break

    return {
        'verdict': verdict,
        'normalized': key,
        'name_matches': name_matches,
        'locality_matches': locality_matches,
        'nearby': nearby[:12],
        'rename_blocked': rename_blocked,
    }
