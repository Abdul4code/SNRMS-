"""Which ward a locality belongs to.

The applicant is not asked for their ward — a locality sits in exactly one ward,
so asking invites a contradiction between the two answers. The council's own
community list (config/data/illg_wards.json) is the authority; the surveyed
buildings are the fallback for estates and layouts that are not on it.

Resolution order, most trustworthy first:
  1. the LGA's official community -> ward list, matched on a normalised name
  2. the ward most often recorded by enumerators for that locality
  3. the ward of the nearest surveyed building, when a location is known
"""
import functools
import json
import os
import re

from django.conf import settings

VALID_WARDS = ('ward_a', 'ward_b', 'ward_c1', 'ward_c2', 'ward_d', 'ward_e', 'ward_f')


def _key(name):
    """Fold a locality name to something two spellings of it can share."""
    s = (name or '').strip().lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


@functools.lru_cache(maxsize=1)
def _official_map():
    path = os.path.join(settings.BASE_DIR, 'config', 'data', 'illg_wards.json')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {_key(name): ward for name, ward in data['community_to_ward'].items()}


def ward_for_locality(locality):
    """The official ward for a locality name, or '' when it is not on the list."""
    if not locality:
        return ''
    official = _official_map()
    key = _key(locality)
    if key in official:
        return official[key]
    # "Abijo GRA", "Awoyaya Town", "Gbetu Road Awoyaya" — a community name with a
    # qualifier attached. Take the longest official name the locality contains, so
    # that "Abijo GRA" matches "Abijo" rather than something shorter and wronger.
    words = set(key.split())
    best, best_len = '', 0
    for name, ward in official.items():
        name_words = name.split()
        if all(w in words for w in name_words) and len(name) > best_len:
            best, best_len = ward, len(name)
    return best


def ward_from_surveys(locality, lat=None, lng=None):
    """Fallback: what the enumerators recorded for this locality, or nearby."""
    from collections import Counter
    from config.models import BuildingSurvey

    if locality:
        votes = Counter(
            w for w in BuildingSurvey.objects
            .filter(locality__iexact=locality.strip())
            .values_list('ward', flat=True)
            if _normalise_ward(w)
        )
        if votes:
            return _normalise_ward(votes.most_common(1)[0][0])

    if lat is not None and lng is not None:
        import math
        best, best_d = '', float('inf')
        window = 0.02                      # ~2 km; keeps the scan small
        for b in (BuildingSurvey.objects
                  .filter(latitude__range=(float(lat) - window, float(lat) + window),
                          longitude__range=(float(lng) - window, float(lng) + window))
                  .exclude(ward='')):
            ward = _normalise_ward(b.ward)
            if not ward or b.latitude is None:
                continue
            d = math.hypot(float(b.latitude) - float(lat), float(b.longitude) - float(lng))
            if d < best_d:
                best, best_d = ward, d
        return best
    return ''


def _normalise_ward(raw):
    """Enumerators wrote "B", "Ward E", "Iwerekun 1" — map those to ward codes."""
    s = (raw or '').strip().lower()
    if not s:
        return ''
    if s in VALID_WARDS:
        return s
    code = re.sub(r'^ward\s*', '', s).replace(' ', '')
    direct = {'a': 'ward_a', 'b': 'ward_b', 'c1': 'ward_c1', 'c2': 'ward_c2',
              'd': 'ward_d', 'e': 'ward_e', 'f': 'ward_f'}
    if code in direct:
        return direct[code]
    for pattern, ward in (
        (r'ibeju\s*(1|i)\b', 'ward_a'), (r'ibeju\s*(2|ii)\b', 'ward_b'),
        (r'orimedu\s*1', 'ward_c1'), (r'orimedu\s*2', 'ward_c2'),
        (r'orimedu\s*3', 'ward_d'),
        (r'iwerekun\s*1', 'ward_e'), (r'iwerekun\s*2', 'ward_f'),
    ):
        if re.search(pattern, s):
            return ward
    return ''


def resolve_ward(locality, lat=None, lng=None, fallback=''):
    """The ward for this application. Never raises; returns `fallback` if unknown."""
    return (ward_for_locality(locality)
            or ward_from_surveys(locality, lat, lng)
            or _normalise_ward(fallback)
            or fallback
            or '')
