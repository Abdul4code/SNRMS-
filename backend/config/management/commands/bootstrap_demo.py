"""One-shot, idempotent setup for a demo: fees + street types, the registered
street registry, and all role accounts (Local Government Chairman, Council
Treasurer, Street Naming Committee). Safe to run on every startup.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.models import User, Role

DEMO_PASSWORD = 'SecurePass123'

# email, first name, last name, role
ACCOUNTS = [
    ('chairman@ibeju-lekki.gov.ng', 'Engr. Hon.', 'Olowa', Role.COMMITTEE_CHAIRMAN),
    ('finance@ibeju-lekki.gov.ng',  'Council',    'Treasurer', Role.FINANCE),
    ('committee@ibeju-lekki.gov.ng', 'Street Naming', 'Committee', Role.NAMING_COMMITTEE),
]


class Command(BaseCommand):
    help = 'Idempotently seed fees/street types, import registered streets, and create role accounts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding street types and fees ==='))
        call_command('seed_data')

        self.stdout.write(self.style.MIGRATE_HEADING('=== Importing registered streets ==='))
        call_command('import_registered_streets')

        self.stdout.write(self.style.MIGRATE_HEADING('=== Building canonical street registry ==='))
        call_command('build_street_registry')

        self.stdout.write(self.style.MIGRATE_HEADING('=== Creating role accounts ==='))
        for email, first, last, role in ACCOUNTS:
            user, _ = User.objects.get_or_create(email=email, defaults={
                'first_name': first, 'last_name': last, 'role': role,
            })
            user.first_name = first
            user.last_name = last
            user.role = role
            user.is_active = True
            if role == Role.COMMITTEE_CHAIRMAN:
                user.is_staff = True
                user.is_superuser = True
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f'  {user.get_role_display()}: {email} (password: {DEMO_PASSWORD})')

        
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seeding Street Naming Committee (7 members) ==='))
        from applications.models import CommitteeMember
        names = {1: 'Committee Chairman', 2: 'Committee Member 2', 3: 'Committee Member 3',
                 4: 'Committee Member 4', 5: 'Committee Member 5', 6: 'Committee Member 6',
                 7: 'Committee Member 7'}
        for n in range(1, 8):
            m, created = CommitteeMember.objects.get_or_create(number=n, defaults={'name': names[n]})
            if created or not m.pin_hash:
                m.name = names[n]
                m.set_pin(f'{n}{n}{n}{n}')  # demo PINs: 1111, 2222, ... 7777
                m.save()
        self.stdout.write('  7 committee members ready (PINs 1111..7777, member 1 = chairman).')

        self.stdout.write(self.style.SUCCESS('Demo bootstrap complete. You can log in now.'))
