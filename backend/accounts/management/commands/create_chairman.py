from django.core.management.base import BaseCommand, CommandError

from accounts.models import Role, User


class Command(BaseCommand):
    help = 'Create a committee chairman user account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email address for the chairman.')
        parser.add_argument('--password', required=True, help='Password for the chairman.')
        parser.add_argument('--first-name', required=True, dest='first_name',
                            help='First name of the chairman.')
        parser.add_argument('--last-name', required=True, dest='last_name',
                            help='Last name of the chairman.')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Warn if a chairman already exists, but proceed anyway.
        existing_chairmen = User.objects.filter(role=Role.COMMITTEE_CHAIRMAN)
        if existing_chairmen.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: {existing_chairmen.count()} committee chairman account(s) already '
                    'exist. A new chairman will still be created.'
                )
            )

        if User.objects.filter(email=email).exists():
            raise CommandError(f'A user with email "{email}" already exists.')

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=Role.COMMITTEE_CHAIRMAN,
                is_staff=True,
            )
        except Exception as exc:
            raise CommandError(f'Failed to create chairman: {exc}') from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created committee chairman: {user.full_name} <{user.email}>'
            )
        )
