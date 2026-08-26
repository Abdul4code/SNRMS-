"""Clearing the test data without clearing the people who made it.

Testers should not have to register again just because their trial
applications were swept up before go-live.
"""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from config.models import StreetType
from payments.models import Payment, PaymentStage, PaymentStatus


class ResetKeepingAccountsTests(TestCase):
    def setUp(self):
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.tester = User.objects.create_user(
            email='tester@example.com', password='x', first_name='T', last_name='R',
            role=Role.APPLICANT)
        self.finance = User.objects.create_user(
            email='fin@example.com', password='x', first_name='F', last_name='N',
            role=Role.FINANCE)
        # The import account the digitised register belongs to.
        User.objects.create_user(
            email='legacy-registry@ibeju-lekki.gov.ng', password='x',
            first_name='Legacy', last_name='Registry', role=Role.APPLICANT)
        self.app = Application.objects.create(
            applicant=self.tester, proposed_street_name='Test', location_description='d',
            street_type=self.st, status=ApplicationStatus.CERTIFICATE_ISSUED)
        Payment.objects.create(application=self.app, stage=PaymentStage.STAGE_A,
                               amount_expected=100, amount_submitted=100,
                               status=PaymentStatus.CONFIRMED)
        self.legacy = Application.objects.create(
            applicant=self.tester, proposed_street_name='Old Street',
            location_description='d', street_type=self.st, is_legacy=True,
            status=ApplicationStatus.CERTIFICATE_ISSUED)

    def run_reset(self, *args):
        out = StringIO()
        call_command('reset_for_golive', *args, stdout=out)
        return out.getvalue()

    def test_the_test_data_goes_but_the_login_stays(self):
        self.run_reset('--yes', '--keep-accounts')
        self.assertFalse(Application.objects.filter(pk=self.app.pk).exists())
        self.assertEqual(Payment.objects.count(), 0, 'the money must read zero')
        self.assertTrue(User.objects.filter(pk=self.tester.pk).exists(),
                        'the tester should not have to register again')

    def test_the_legacy_register_is_untouched(self):
        self.run_reset('--yes', '--keep-accounts')
        self.assertTrue(Application.objects.filter(pk=self.legacy.pk).exists())

    def test_staff_are_kept_as_always(self):
        self.run_reset('--yes', '--keep-accounts')
        self.assertTrue(User.objects.filter(pk=self.finance.pk).exists())

    def test_the_report_says_no_account_will_go(self):
        out = self.run_reset('--dry-run', '--keep-accounts')
        self.assertIn('applicant accounts       : 0', out)
        self.assertIn('every login stays', out)
        self.assertTrue(Application.objects.filter(pk=self.app.pk).exists(),
                        'a dry run must delete nothing')

    def test_without_the_flag_the_account_still_goes(self):
        """The default behaviour is unchanged."""
        self.run_reset('--yes', '--reassign-legacy')
        self.assertFalse(User.objects.filter(pk=self.tester.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.finance.pk).exists())
