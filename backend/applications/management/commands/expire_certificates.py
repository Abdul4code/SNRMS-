from django.core.management.base import BaseCommand
from django.utils import timezone

from applications.models import Application, ApplicationStatus
from notifications.models import NotificationType
from applications.services import notify_applicant


class Command(BaseCommand):
    help = 'Transition certificate_issued applications to expired when their expiry date has passed.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        due = Application.objects.filter(
            status=ApplicationStatus.CERTIFICATE_ISSUED,
            expires_at__lte=today,
            is_deleted=False,
        )
        count = 0
        for app in due:
            try:
                app.transition_to(
                    ApplicationStatus.EXPIRED,
                    actor=None,
                    remarks='Certificate expired automatically.',
                )
                notify_applicant(
                    app,
                    notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
                    title='Certificate Expired',
                    message=(
                        f'Your street naming certificate for application {app.reference_number} '
                        f'expired on {app.expires_at.strftime("%d %B %Y")}. '
                        'Please renew to keep your registration active.'
                    ),
                )
                count += 1
            except ValueError:
                pass
        self.stdout.write(self.style.SUCCESS(f'Expired {count} certificate(s).'))
