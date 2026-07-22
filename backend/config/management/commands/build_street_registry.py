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
    def handle(self, *args, **options):
        # Rebuild only the auto (survey-derived) layer; never touch digitised
        # ground-truth streets that were imported from a proper survey.
        auto = Street.objects.filter(source=Street.SOURCE_SURVEY)
        BuildingSurvey.objects.filter(street__in=auto).update(street=None)
        auto.delete()
        if Street.objects.filter(source=Street.SOURCE_DIGITISED).exists():
            self.stdout.write('Preserved existing digitised (ground-truth) streets.')

        street_types = {st.name: st for st in StreetType.objects.all()}

        # Group buildings by normalized street name.
        groups = defaultdict(list)
        unnamed = 0
        for b in BuildingSurvey.objects.all():
            raw = (b.existing_street_name or '').strip()
            if raw.lower() in UNNAMED_TOKENS:
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
            raw_names = Counter((b.existing_street_name or '').strip() for b in buildings)
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
            def _in_bounds(la, lo):
                return la is not None and lo is not None and 6.2 <= float(la) <= 6.85 and 3.4 <= float(lo) <= 4.5
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
