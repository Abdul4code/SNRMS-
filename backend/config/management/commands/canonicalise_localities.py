"""Put every stored locality under the name the council uses for that place.

The survey, the old street register and the applications each spell the same
community their own way — Ayeteju and Aiyeteju, Gbogije and Bogije, Abidjan and
Abijo. Until they agree, a locality filter misses streets and the same place is
counted twice.

    python manage.py canonicalise_localities --dry-run
    python manage.py canonicalise_localities
"""
import collections

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.localities import canonical_locality
from applications.models import Application
from applications.wards import resolve_ward
from config.models import BuildingSurvey, Street


class Command(BaseCommand):
    help = 'Rewrite stored localities to the council\'s community names.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change; write nothing.')

    def handle(self, *args, **options):
        dry = options['dry_run']
        changes = collections.Counter()
        wards_fixed = 0

        for model, label in ((BuildingSurvey, 'survey buildings'),
                             (Street, 'registry streets'),
                             (Application, 'applications')):
            rows = model.objects.exclude(locality='')
            edits = []
            for row in rows:
                canon = canonical_locality(row.locality)
                if canon and canon != row.locality:
                    changes[f'{row.locality} -> {canon}'] += 1
                    row.locality = canon
                    edits.append(row)
            self.stdout.write(f'{label}: {len(edits)} of {rows.count()} renamed')
            if edits and not dry:
                with transaction.atomic():
                    model.objects.bulk_update(edits, ['locality'], batch_size=500)

        # A ward derived from a misspelling may have missed; re-derive where the
        # locality now resolves to one and the application disagrees.
        for app in Application.objects.exclude(locality=''):
            ward = resolve_ward(app.locality, app.latitude, app.longitude, fallback=app.ward)
            if ward and ward != app.ward:
                wards_fixed += 1
                if not dry:
                    app.ward = ward
                    app.save(update_fields=['ward', 'updated_at'])

        self.stdout.write('')
        self.stdout.write(f'wards corrected: {wards_fixed}')
        self.stdout.write('')
        self.stdout.write('most common renames:')
        for change, n in changes.most_common(15):
            self.stdout.write(f'   {change}  x{n}')
        if dry:
            self.stdout.write(self.style.WARNING('\nDry run: nothing was written.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nLocalities now match the community list.'))
