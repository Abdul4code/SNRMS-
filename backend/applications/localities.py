"""One name per place.

The council's community list (config/data/illg_wards.json) is the authority on
what a locality is called. Everything else — the field survey, the old street
register, whatever an applicant typed — arrives spelled its own way: Ayeteju and
Aiyeteju, Shappatti and Shapati, Gbogije and Bogije, Abidjan and Abijo. Left
alone, the same place counts as several, so a locality filter misses streets and
a ward is derived from a name nobody official recognises.

config/data/community_aliases.json maps every spelling seen in the survey and the
register onto the community it belongs to. Most were settled by name; the rest by
where their buildings actually are — a locality whose buildings sit within half a
kilometre of a community's buildings is that community under another spelling.

Two names in the survey are real places the council's list does not carry —
Igbojia (142 buildings) and Majek (51). They map to themselves rather than being
folded into a neighbour, and are listed in ADDITIONS so the council can rule on
them.
"""
import functools
import json
import os
import re

from django.conf import settings

# Real settlements the survey found that the official list does not name. Kept as
# themselves rather than absorbed into whichever community happens to be nearest.
ADDITIONS = ('Igbojia', 'Majek')


def _fold(name):
    """Fold a locality name so two spellings of it compare equal."""
    s = re.sub(r'[^a-z0-9]+', ' ', (name or '').lower())
    return re.sub(r'\s+', ' ', s).strip()


@functools.lru_cache(maxsize=1)
def _aliases():
    path = os.path.join(settings.BASE_DIR, 'config', 'data', 'community_aliases.json')
    try:
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    return {_fold(k): v for k, v in raw.items()}


@functools.lru_cache(maxsize=1)
def official_communities():
    """The council's own list, plus the places the survey proves exist."""
    path = os.path.join(settings.BASE_DIR, 'config', 'data', 'illg_wards.json')
    with open(path, encoding='utf-8') as f:
        names = list(json.load(f)['community_to_ward'])
    return sorted(set(names) | set(ADDITIONS))


def canonical_locality(name):
    """The community this spelling belongs to, or the name unchanged if unknown.

    Never invents: a locality nobody has seen before is returned as given, so an
    applicant is not silently filed under somewhere else.
    """
    if not name:
        return ''
    folded = _fold(name)
    hit = _aliases().get(folded)
    if hit:
        return hit
    for community in official_communities():
        if _fold(community) == folded:
            return community
    return name.strip()


def is_official(name):
    """Whether this locality is one the council recognises."""
    return canonical_locality(name) in set(official_communities())
