"""Transfer street NAMES from survey points onto the digitised street network.

The digitised centre-lines are the ground truth for geometry; the raw survey
points are used ONLY to supply names. Each named survey point is snapped to the
nearest digitised street within a tolerance, and each street takes the most
common name among the points that snapped to it.
"""
import json
import math
from collections import defaultdict, Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from config.models import Street, BuildingSurvey

UNNAMED_TOKENS = {'', 'none', 'na', 'n/a', 'nil', 'null', 'no', 'nan', '-', '.', 'none.'}
SNAP_TOLERANCE_M = 40.0        # a point farther than this from any line is ignored
# Local metres-per-degree around Ibeju-Lekki (~lat 6.47).
M_PER_DEG_LAT = 110574.0
M_PER_DEG_LNG = 111320.0 * math.cos(math.radians(6.47))


def _pt_seg_dist_m(plat, plng, alat, alng, blat, blng):
    """Distance (metres) from point P to segment AB, using a local planar approx."""
    px, py = plng * M_PER_DEG_LNG, plat * M_PER_DEG_LAT
    ax, ay = alng * M_PER_DEG_LNG, alat * M_PER_DEG_LAT
    bx, by = blng * M_PER_DEG_LNG, blat * M_PER_DEG_LAT
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


class Command(BaseCommand):
    help = 'Snap named survey points onto digitised streets to transfer street names.'

    def add_arguments(self, parser):
        parser.add_argument('--tolerance', type=float, default=SNAP_TOLERANCE_M)

    @transaction.atomic
    def handle(self, *args, **options):
        tol = options['tolerance']
        # Load digitised streets with geometry, precompute a bbox for pre-filtering.
        streets = []
        for st in Street.objects.filter(source=Street.SOURCE_DIGITISED).exclude(geometry=''):
            try:
                coords = json.loads(st.geometry).get('coordinates', [])
            except (json.JSONDecodeError, AttributeError):
                continue
            if len(coords) < 2:
                continue
            lats = [c[1] for c in coords]
            lngs = [c[0] for c in coords]
            streets.append({
                'obj': st, 'coords': coords,
                'bbox': (min(lats), max(lats), min(lngs), max(lngs)),
            })
        if not streets:
            self.stdout.write(self.style.WARNING(
                'No digitised streets found. Run import_streets_geojson first.'))
            return

        pad = tol / M_PER_DEG_LAT * 1.5  # bbox padding in degrees
        name_votes = defaultdict(Counter)
        BuildingSurvey.objects.filter(street__source=Street.SOURCE_DIGITISED).update(street=None)

        matched = 0
        for b in BuildingSurvey.objects.exclude(latitude=None).exclude(longitude=None):
            raw = (b.existing_street_name or '').strip()
            if raw.lower() in UNNAMED_TOKENS:
                continue
            plat, plng = float(b.latitude), float(b.longitude)
            if not (6.2 <= plat <= 6.85 and 3.4 <= plng <= 4.5):
                continue  # skip corrupt coordinates
            best, best_d = None, tol
            for s in streets:
                mnla, mxla, mnlo, mxlo = s['bbox']
                if plat < mnla - pad or plat > mxla + pad or plng < mnlo - pad or plng > mxlo + pad:
                    continue
                c = s['coords']
                d = min(
                    _pt_seg_dist_m(plat, plng, c[i][1], c[i][0], c[i + 1][1], c[i + 1][0])
                    for i in range(len(c) - 1)
                )
                if d < best_d:
                    best_d, best = d, s
            if best is not None:
                name_votes[best['obj'].id][raw] += 1
                BuildingSurvey.objects.filter(pk=b.pk).update(street=best['obj'])
                matched += 1

        # Assign each street its winning name (only if it had no digitised name already).
        named = 0
        for s in streets:
            votes = name_votes.get(s['obj'].id)
            if not votes:
                continue
            winner = votes.most_common(1)[0][0].strip().title()
            st = s['obj']
            if not st.name or st.name.lower().startswith('unnamed'):
                st.name = winner
            st.building_count = BuildingSurvey.objects.filter(street=st).count()
            st.save(update_fields=['name', 'building_count'])
            named += 1

        self.stdout.write(self.style.SUCCESS(
            f'Name transfer complete — {matched} points snapped to {len(streets)} digitised '
            f'streets; {named} streets received a name from the survey.'
        ))
