"""Send one test email to prove the configured mail provider works.

    python manage.py send_test_email you@example.com

Reports which backend is active and, on failure, the provider's own error —
which is where SendGrid says things like "from address does not match a
verified Sender Identity".
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Send a test email to confirm the mail provider is configured correctly.'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Address to send the test message to')

    def handle(self, *args, **options):
        recipient = options['recipient']

        self.stdout.write(f'Backend:   {settings.EMAIL_BACKEND}')
        self.stdout.write(f'From:      {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To:        {recipient}')
        if 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                'No provider configured — the message will only print below, not send. '
                'Set SENDGRID_API_KEY to send for real.'))
        self.stdout.write('')

        mail = EmailMultiAlternatives(
            subject='[Ibeju-Lekki SNRMS] Test email',
            body='This is a test message from SNRMS. If you received it, email delivery works.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        mail.attach_alternative(
            '<p>This is a test message from <strong>SNRMS</strong>. '
            'If you received it, email delivery works.</p>', 'text/html')

        try:
            sent = mail.send(fail_silently=False)
        except Exception as exc:  # noqa: BLE001 - surface the provider's own message
            raise CommandError(f'{type(exc).__name__}: {exc}') from exc

        if not sent:
            raise CommandError('The backend accepted no messages.')
        self.stdout.write(self.style.SUCCESS(f'Sent. Check {recipient} (including spam).'))
