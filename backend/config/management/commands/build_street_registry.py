"""Build the canonical Street registry from surveyed buildings.

De-duplicates the free-text street names captured during the survey (fixing
case, spacing, punctuation and common abbreviations/misspellings), creates one
Street record per real street, and links every building to its street. Streets
that already have a registered Application are marked 'registered'.
"""
import re
from collections import defaultdict, Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from config.models import BuildingSurvey, Street, StreetType

# Values enumerators used to mean "no name".
UNNAMED_TOKENS = {'', 'none', 'na', 'n/a', 'nil', 'null', 'no', 'nan', '-', '.', 'none.'}

# Common abbreviations / misspellings → canonical street-type word.
TYPE_FIX = {
    'streeet': 'street', 'stret': 'street', 'steet': 'street', 'strt': 'street',
    'str': 'street', 'st': 'street',
    'rd': 'road', 'ave': 'avenue', 'av': 'avenue',
    'cres': 'crescent', 'cresent': 'crescent', 'cr': 'crescent',
    'cl': 'close', 'clse': 'close', 'dr': 'drive', 'ln': 'lane',
    'blvd': 'boulevard', 'ct': 'court',
}

TYPE_WORDS = {
    'street': 'Street', 'road': 'Road', 'close': 'Close', 'avenue': 'Avenue',
    'crescent': 'Crescent', 'drive': 'Drive', 'lane': 'Lane', 'way': 'Way',
    'boulevard': 'Boulevard', 'court': 'Court', 'terrace': 'Terrace',
    'gardens': 'Gardens', 'grove': 'Grove', 'mews': 'Mews', 'place': 'Place',
    'parkway': 'Parkway', 'esplanade': 'Esplanade', 'circus': 'Circus', 'plaza': 'Plaza',
}


def _in_bounds(la, lo):
    return la is not None and lo is not None and 6.2 <= float(la) <= 6.85 and 3.4 <= float(lo) <= 4.5


def _initials_compatible(k1, k2):
    """True if one name is an abbreviation of the other — e.g. "abayomi o" vs
    "abayomi odufuwa" (surname shortened to its initial). Tokens are aligned from
    the start; each aligned pair must be equal or one a prefix/initial of the other,
    and the first token must be a full, matching word to anchor it."""
    t1, t2 = k1.split(), k2.split()
    if not t1 or not t2:
        return False
    short, long = (t1, t2) if len(t1) <= len(t2) else (t2, t1)
    if len(short[0]) <= 1 or short[0] != long[0]:
        return False  # must share a real first word
    for i, tok in enumerate(short):
        if i >= len(long):
            return False
        lt = long[i]
        if tok == lt or lt.startswith(tok) or tok.startswith(lt):
            continue
        return False
    # require at least one abbreviation (otherwise it's just a shorter distinct name)
    return short != long[:len(short)] or len(short) < len(long)


def normalize(raw: str) -> str:
    """Return a normalized key used to merge spelling variants of one street."""
    s = (raw or '').strip().lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)        # drop punctuation
    s = re.sub(r'\s+', ' ', s).strip()
    tokens = [TYPE_FIX.get(t, t) for t in s.split()]
    return ' '.join(tokens)


class Command(BaseCommand):
    help = 'Build the canonical Street registry from building survey data.'

    @transaction.atomic
    def add_arguments(self, parser):
        parser.add_argument(
            '--infer-radius', type=float, default=35.0,
            help='Distance (metres) along the street for majority-vote naming of blank '
                 'building points, following the line of named points. 0 disables. Default: 35.')
        parser.add_argument(
            '--no-merge', action='store_true',
            help='Disable the fuzzy + spatial near-duplicate street-name merge pass.')

    def handle(self, *args, **options):
        self._infer_radius = options.get('infer_radius', 35.0)
        self._do_fuzzy_merge = not options.get('no_merge', False)
        # Rebuild only the auto (survey-derived) layer; never touch digitised
        # ground-truth streets that were imported from a proper survey.
        auto = Street.objects.filter(source=Street.SOURCE_SURVEY)
        BuildingSurvey.objects.filter(street__in=auto).update(street=None)
        auto.delete()
        if Street.objects.filter(source=Street.SOURCE_DIGITISED).exists():
            self.stdout.write('Preserved existing digitised (ground-truth) streets.')

        street_types = {st.name: st for st in StreetType.objects.all()}

        # --- Interim majority-vote naming (no digitised lines needed) ---------
        # A building whose name field was left blank often sits on a street that
        # IS named — the enumerator simply didn't fill it in. We rescue these by
        # majority vote of the *named* survey points within INFER_RADIUS metres.
        # This never overwrites a name the enumerator did record; it only fills
        # blanks, and only when there is nearby agreement. Radius is configurable
        # (--infer-radius 0 disables).
        import math as _math
        from collections import Counter as _Counter
        INFER_RADIUS = getattr(self, '_infer_radius', 30.0)
        inferred = {}   # kobo_id -> inferred raw name
        rescued_count = 0
        if INFER_RADIUS and INFER_RADIUS > 0:
            named_pts, blank_pts = [], []
            for b in BuildingSurvey.objects.all():
                if not _in_bounds(b.latitude, b.longitude):
                    continue
                raw = (b.existing_street_name or '').strip()
                rec = (float(b.latitude), float(b.longitude), raw, b.kobo_id)
                if raw.lower() in UNNAMED_TOKENS:
                    blank_pts.append(rec)
                else:
                    named_pts.append(rec)
            # spatial grid over named points for fast neighbour lookup
            cell = INFER_RADIUS / 111000.0
            grid = defaultdict(list)
            for rec in named_pts:
                grid[(round(rec[0] / cell), round(rec[1] / cell))].append(rec)

            def _m(a_lat, a_lng, b_lat, b_lng):
                dlat = (a_lat - b_lat) * 111000
                dlng = (a_lng - b_lng) * 111000 * _math.cos(_math.radians(a_lat))
                return _math.hypot(dlat, dlng)

            for lat, lng, _raw, kid in blank_pts:
                gx, gy = round(lat / cell), round(lng / cell)
                votes = _Counter()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for nlat, nlng, nraw, _k in grid.get((gx + dx, gy + dy), []):
                            d = _m(lat, lng, nlat, nlng)
                            if d <= INFER_RADIUS:
                                # closer points count for more (inverse-distance weight)
                                votes[nraw] += 1.0 / (1.0 + d)
                if votes:
                    inferred[kid] = votes.most_common(1)[0][0]
                    rescued_count += 1
            self.stdout.write(
                f'Majority-vote naming: rescued {rescued_count} blank points within '
                f'{INFER_RADIUS:.0f} m of a named street.')

        # Group buildings by normalized street name (using inferred names for blanks).
        groups = defaultdict(list)
        unnamed = 0
        for b in BuildingSurvey.objects.all():
            raw = (b.existing_street_name or '').strip()
            if raw.lower() in UNNAMED_TOKENS:
                raw = inferred.get(b.kobo_id, '')
            if not raw or raw.lower() in UNNAMED_TOKENS:
                unnamed += 1
                continue
            groups[normalize(raw)].append(b)

        # Trim obvious duplications: a bare-name group (e.g. "02 s") folds into its
        # unique typed counterpart (e.g. "02 s close"), since they are the same street.
        type_set = set(TYPE_WORDS.keys())
        typed_by_base = defaultdict(list)
        for k in list(groups.keys()):
            toks = k.split()
            if len(toks) >= 2 and toks[-1] in type_set:
                typed_by_base[' '.join(toks[:-1])].append(k)
        for k in list(groups.keys()):
            toks = k.split()
            if not toks or toks[-1] in type_set:
                continue  # already typed, or empty
            candidates = typed_by_base.get(k, [])
            if len(candidates) == 1 and k in groups:
                groups[candidates[0]].extend(groups.pop(k))

        # Harmonise abbreviated names: "chief alex osifo" and "chief a osifo" are
        # the same street. Two keys merge when they have the same number of tokens,
        # the LAST token (surname/type) matches exactly, and every other token pair
        # is either equal or one is an initial of the other. Union-find clusters them.
        def _initial_compatible(a_toks, b_toks):
            if len(a_toks) != len(b_toks) or len(a_toks) < 2:
                return False
            if a_toks[-1] != b_toks[-1]:      # anchor on the final token
                return False
            any_full = False
            for x, y in zip(a_toks[:-1], b_toks[:-1]):
                if x == y:
                    any_full = any_full or len(x) > 1
                elif len(x) == 1 and y.startswith(x):
                    pass
                elif len(y) == 1 and x.startswith(y):
                    pass
                else:
                    return False
            return True

        keys = list(groups.keys())
        parent = {k: k for k in keys}

        def _find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        # Compare only keys that share the same last token (keeps it fast + safe).
        from collections import defaultdict as _dd
        by_last = _dd(list)
        for k in keys:
            by_last[k.split()[-1]].append(k)
        for group_keys in by_last.values():
            for i in range(len(group_keys)):
                for j in range(i + 1, len(group_keys)):
                    a, b = group_keys[i], group_keys[j]
                    if _initial_compatible(a.split(), b.split()):
                        parent[_find(a)] = _find(b)
        clusters = _dd(list)
        for k in keys:
            clusters[_find(k)].append(k)
        for members in clusters.values():
            if len(members) < 2:
                continue
            # Canonical = the key with the most full (non-initial) words.
            def _fullness(key):
                return sum(1 for t in key.split() if len(t) > 1)
            keep = max(members, key=lambda m: (_fullness(m), len(groups.get(m, []))))
            for m in members:
                if m != keep and m in groups:
                    groups[keep].extend(groups.pop(m))

        # --- Fuzzy + spatial near-duplicate merge -----------------------------
        # Merge groups whose names are near-matches (typos like Ajegunle/Ajejunle,
        # Street/Stress, Road/Raid/Riad) AND whose buildings are spatially close.
        # "Close" uses the NEAREST distance between the two groups' points (which
        # follows the street line), not the centroid — a long street can have a far
        # centroid but adjacent buildings. Runs unless --no-merge is given.
        if getattr(self, '_do_fuzzy_merge', True):
            import difflib
            merge_keys = list(groups.keys())
            # points per group + a coarse spatial index (~80 m cells)
            gpts = {}
            for k in merge_keys:
                gpts[k] = [(float(b.latitude), float(b.longitude))
                           for b in groups[k]
                           if _in_bounds(b.latitude, b.longitude)]
            SCELL = 0.0007  # ~80 m
            cell_groups = defaultdict(set)
            for k in merge_keys:
                for lat, lng in gpts[k]:
                    cell_groups[(round(lat / SCELL), round(lng / SCELL))].add(k)

            def _near_m(la, lo, lb, lp):
                dlat = (la - lb) * 111000
                dlng = (lo - lp) * 111000 * _math.cos(_math.radians(la))
                return _math.hypot(dlat, dlng)

            def _nearest_between(k1, k2):
                best = 1e9
                for a in gpts[k1]:
                    for b in gpts[k2]:
                        d = _near_m(a[0], a[1], b[0], b[1])
                        if d < best:
                            best = d
                            if best < 1:
                                return best
                return best

            # candidate pairs: groups sharing or adjacent to a cell
            candidates = set()
            for k in merge_keys:
                cells = {(round(lat / SCELL), round(lng / SCELL)) for lat, lng in gpts[k]}
                neigh = set()
                for (cx, cy) in cells:
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            neigh |= cell_groups.get((cx + dx, cy + dy), set())
                for other in neigh:
                    if other != k:
                        candidates.add(tuple(sorted((k, other))))

            fparent = {k: k for k in merge_keys}
            def _ff(x):
                while fparent[x] != x:
                    fparent[x] = fparent[fparent[x]]
                    x = fparent[x]
                return x

            merges = 0
            for k1, k2 in candidates:
                if not gpts[k1] or not gpts[k2]:
                    continue
                ratio = difflib.SequenceMatcher(None, k1, k2).ratio()
                abbr = _initials_compatible(k1, k2)
                if ratio < 0.82 and not abbr:
                    continue
                d = _nearest_between(k1, k2)
                # Near-match names OR an abbreviation, that are also spatially plausible
                # for a single street.
                if (d <= 60 and ratio >= 0.82) or (d <= 110 and ratio >= 0.90) or (d <= 60 and abbr):
                    fparent[_ff(k1)] = _ff(k2)
                    merges += 1

            fclusters = defaultdict(list)
            for k in merge_keys:
                fclusters[_ff(k)].append(k)
            for members in fclusters.values():
                if len(members) < 2:
                    continue
                # Keep the name with the most buildings, preferring one that ends
                # in a real street-type word (e.g. "…Street" over "…Stress").
                def _score(m):
                    toks = m.split()
                    has_type = toks[-1] in TYPE_WORDS if toks else False
                    fullness = sum(1 for t in toks if len(t) > 1)
                    return (has_type, len(groups.get(m, [])), fullness)
                keep = max(members, key=_score)
                for m in members:
                    if m != keep and m in groups:
                        groups[keep].extend(groups.pop(m))
            if merges:
                self.stdout.write(f'Fuzzy+spatial merge: combined {merges} near-duplicate name pairs.')

        # Which normalized names already have a registered application?
        # (Legacy/registered street names, normalized the same way.)
        from applications.models import Application, ApplicationStatus
        registered_keys = set()
        registered_statuses = {
            ApplicationStatus.CERTIFICATE_ISSUED, ApplicationStatus.RENEWED,
            ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
        }
        for a in Application.objects.all():
            full = f'{a.proposed_street_name} {a.street_type.name if a.street_type else ""}'
            if a.status in registered_statuses:
                registered_keys.add(normalize(full))
                registered_keys.add(normalize(a.proposed_street_name))

        streets_created = 0
        # Start numbering after any existing (digitised) street codes to avoid clashes.
        seq = 0
        last = Street.objects.order_by('-code').values_list('code', flat=True).first()
        if last and last.startswith('IBJ-ST-'):
            try:
                seq = int(last.rsplit('-', 1)[1])
            except ValueError:
                seq = Street.objects.count()
        for key, buildings in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            # Canonical display name = most common original spelling in the group.
            # Choose the canonical display name from the REAL names in the group,
            # ignoring buildings whose name was blank/None (including any rescued by
            # the majority-vote pass) so a blank can never win the display name.
            raw_names = Counter(
                (b.existing_street_name or '').strip()
                for b in buildings
                if (b.existing_street_name or '').strip().lower() not in UNNAMED_TOKENS
            )
            if not raw_names:
                # Fall back to the inferred name for a group made purely of rescued blanks.
                raw_names = Counter(
                    inferred[b.kobo_id] for b in buildings if b.kobo_id in inferred
                )
            display = raw_names.most_common(1)[0][0]
            display = re.sub(r'\s+', ' ', display).strip().title()

            # Detect street type from the last normalized token, if known.
            last = key.split()[-1] if key.split() else ''
            st = street_types.get(TYPE_WORDS.get(last, ''))

            # Most common ward / locality in the group.
            ward = Counter(b.ward for b in buildings if b.ward).most_common(1)
            locality = Counter(b.locality for b in buildings if b.locality).most_common(1)

            seq += 1
            reg = (
                Street.RegistrationStatus.REGISTERED
                if key in registered_keys
                else Street.RegistrationStatus.SURVEYED
            )
            # Centroid from member building coordinates (georeference).
            # Ignore corrupt GPS points outside the Ibeju-Lekki area.
            coords = [(b.latitude, b.longitude) for b in buildings if _in_bounds(b.latitude, b.longitude)]
            clat = sum(c[0] for c in coords) / len(coords) if coords else None
            clng = sum(c[1] for c in coords) / len(coords) if coords else None
            street = Street.objects.create(
                name=display,
                normalized_key=key,
                code=f'IBJ-ST-{seq:04d}',
                street_type=st,
                ward=ward[0][0] if ward else '',
                locality=locality[0][0] if locality else '',
                building_count=len(buildings),
                name_variants=len(raw_names),
                registration_status=reg,
                validation_status=Street.VALIDATION_SURVEY,
                latitude=clat,
                longitude=clng,
            )
            # Link buildings.
            ids = [b.kobo_id for b in buildings]
            BuildingSurvey.objects.filter(kobo_id__in=ids).update(street=street)
            streets_created += 1

        merged_from = sum(s.name_variants for s in Street.objects.all())
        registered = Street.objects.filter(
            registration_status=Street.RegistrationStatus.REGISTERED
        ).count()
        self.stdout.write(self.style.SUCCESS(
            f'Street registry built — {streets_created} canonical streets '
            f'(merged from {merged_from} raw spellings), {registered} registered. '
            f'{unnamed} buildings remain on unnamed streets.'
        ))

        # --- Ingest named streets from the OLD REGISTRY that aren't yet in the DB ---
        # Any registered / legacy application whose street name has no matching Street
        # record is georeferenced from the application's own coordinates and added,
        # tagged "collected from old registry". Survey records take precedence: if the
        # normalized name already exists (from the survey pass), we DON'T override it.
        from applications.models import Application
        existing_keys = set(Street.objects.values_list('normalized_key', flat=True))
        reg_seq = seq
        registry_added = 0
        seen = set()
        registry_apps = (
            Application.objects.filter(is_deleted=False)
            .exclude(proposed_street_name='')
            .filter(status__in=[
                ApplicationStatus.CERTIFICATE_ISSUED, ApplicationStatus.RENEWED,
                ApplicationStatus.RENEWAL_PAYMENT_CONFIRMED,
            ])
        )
        for a in registry_apps:
            key = normalize(a.proposed_street_name)
            if not key or key in existing_keys or key in seen:
                continue  # survey/registry duplicate — survey overrides, so skip
            seen.add(key)
            reg_seq += 1
            Street.objects.create(
                name=re.sub(r'\s+', ' ', a.proposed_street_name).strip().title(),
                normalized_key=key,
                code=f'IBJ-ST-{reg_seq:04d}',
                street_type=a.street_type,
                ward=a.ward or '',
                locality=a.locality or '',
                building_count=0,
                name_variants=1,
                registration_status=Street.RegistrationStatus.REGISTERED,
                validation_status=Street.VALIDATION_REGISTRY,
                latitude=a.latitude,
                longitude=a.longitude,
            )
            registry_added += 1

        # --- Seed known named streets that aren't in the survey/registry ----------
        # Streets the Council knows exist (e.g. beside the Secretariat) but which the
        # enumerators didn't capture. Ward is inferred from the nearest survey point.
        SEED_STREETS = [
            # Sanwo-Olu Street — the tarred road beside the LG Secretariat (Efiran).
            {'name': 'Sanwo-Olu', 'lat': 6.470815, 'lng': 3.808070, 'type': 'Street',
             'locality': 'Efiran'},
        ]
        all_pts = [
            (b.latitude, b.longitude, b.ward)
            for b in BuildingSurvey.objects.all()
            if _in_bounds(b.latitude, b.longitude)
        ]

        def _nearest_ward(lat, lng):
            best, bw = 1e18, ''
            for pl, pn, pw in all_pts:
                d = (float(pl) - lat) ** 2 + (float(pn) - lng) ** 2
                if d < best:
                    best, bw = d, (pw or '')
            return bw

        seed_seq = reg_seq
        seeded = 0
        updated_seed = 0
        for sd in SEED_STREETS:
            key = normalize(sd['name'])
            if not key:
                continue
            # If a street already carries this name (e.g. "Babajide Sanwo-Olu"),
            # geolocate THAT one instead of creating a duplicate.
            existing = (Street.objects.filter(normalized_key=key).first()
                        or Street.objects.filter(normalized_key__contains=key).first())
            if existing:
                changed = []
                if existing.latitude is None or existing.longitude is None:
                    existing.latitude = sd['lat']; existing.longitude = sd['lng']; changed += ['latitude', 'longitude']
                if not existing.locality and sd.get('locality'):
                    existing.locality = sd['locality']; changed += ['locality']
                if existing.registration_status != Street.RegistrationStatus.REGISTERED:
                    existing.registration_status = Street.RegistrationStatus.REGISTERED; changed += ['registration_status']
                if changed:
                    existing.save(update_fields=changed)
                    updated_seed += 1
                continue
            seed_seq += 1
            st = None
            try:
                from config.models import StreetType as _ST
                st = _ST.objects.filter(name__iexact=sd.get('type', 'Street')).first() or _ST.objects.first()
            except Exception:  # noqa: BLE001
                pass
            Street.objects.create(
                name=sd['name'].strip().title(),
                normalized_key=key,
                code=f'IBJ-ST-{seed_seq:04d}',
                street_type=st,
                ward=_nearest_ward(sd['lat'], sd['lng']),
                locality=sd.get('locality', ''),
                building_count=0,
                name_variants=1,
                registration_status=Street.RegistrationStatus.REGISTERED,
                validation_status=Street.VALIDATION_REGISTRY,
                latitude=sd['lat'],
                longitude=sd['lng'],
            )
            seeded += 1
        if seeded or updated_seed:
            self.stdout.write(self.style.SUCCESS(
                f'Seeded {seeded} and geolocated {updated_seed} known street(s) '
                f'(e.g. Sanwo-Olu, beside the Secretariat).'))

        # --- Category report (chat only, not a dashboard) ------------------------
        g = Street.objects.filter(validation_status=Street.VALIDATION_GOOGLE).count()
        s_ = Street.objects.filter(validation_status=Street.VALIDATION_SURVEY).count()
        r_ = Street.objects.filter(validation_status=Street.VALIDATION_REGISTRY).count()
        self.stdout.write(self.style.WARNING(
            '── Street provenance categories ──\n'
            f'  Validation urgently required (Google Earth): {g}\n'
            f'  Needs regularization (survey):               {s_}\n'
            f'  Collected from old registry:                 {r_}  (+{registry_added} added this run)\n'
            f'  TOTAL streets in database:                   {g + s_ + r_}'
        ))
