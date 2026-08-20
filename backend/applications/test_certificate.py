"""The certificate is the thing the applicant frames and the Council stands
behind, so its term and its layout are both checked here.

The layout tests read the generated PDF back with pdfplumber, which is a
test-only tool and not a runtime dependency. They skip when it is absent:
    pip install pdfplumber
"""
import datetime
import unittest

from django.test import TestCase
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

from accounts.models import Role, User
from applications.certificates import generate_certificate_pdf
from applications.models import Application, ApplicationStatus
from applications.services import issue_certificate
from config.models import StreetType

PAGE_W, _ = landscape(A4)
BORDER_L, BORDER_R = 15 * mm, PAGE_W - 15 * mm   # the gold rule on the page


class CertificateTermTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cert@example.com', password='x', first_name='Test',
            last_name='Glory', role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Close', code='CL')

    def _ready_application(self):
        return Application.objects.create(
            applicant=self.user, proposed_street_name='Glory',
            location_description='d', street_type=self.st, ward='ward_b',
            locality='Ibeju-Lego/000103', status=ApplicationStatus.STAGE_C_CONFIRMED)

    def test_a_certificate_runs_five_years_from_issue(self):
        app = self._ready_application()
        issue_certificate(app, actor=self.user)
        app.refresh_from_db()
        issued = app.certificate_issued_at.date()
        self.assertEqual(app.expires_at, issued.replace(year=issued.year + 5))

    def test_five_years_is_the_same_calendar_day_not_1825_days(self):
        """5 x 365 loses a day to each leap year, ending the term early."""
        app = self._ready_application()
        issue_certificate(app, actor=self.user)
        app.refresh_from_db()
        issued = app.certificate_issued_at.date()
        naive = issued + datetime.timedelta(days=5 * 365)
        self.assertGreaterEqual(app.expires_at, naive)
        self.assertEqual(app.expires_at.day, issued.day)
        self.assertEqual(app.expires_at.month, issued.month)

    def test_an_explicit_expiry_still_wins(self):
        app = self._ready_application()
        chosen = datetime.date(2028, 3, 1)
        issue_certificate(app, actor=self.user, expires_at=chosen)
        app.refresh_from_db()
        self.assertEqual(app.expires_at, chosen)


try:
    import pdfplumber
    HAVE_PDFPLUMBER = True
except ImportError:                       # pragma: no cover
    HAVE_PDFPLUMBER = False


@unittest.skipUnless(HAVE_PDFPLUMBER, 'pdfplumber is needed to read the PDF back')
class CertificateLayoutTests(TestCase):
    """Nothing may cross the border — "VALID UNTIL" used to run off the page."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='layout@example.com', password='x', first_name='Test',
            last_name='Glory', role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')

    def _render(self, name, locality, holder):
        self.user.first_name, self.user.last_name = holder
        self.user.save()
        app = Application.objects.create(
            applicant=self.user, proposed_street_name=name, location_description='d',
            street_type=self.st, ward='ward_b', locality=locality,
            status=ApplicationStatus.STAGE_C_CONFIRMED)
        app.certificate_number = 'CERT-2026-00001'
        app.signboard_number = 'SB-001'
        app.pole_number = 'PL-001'
        app.certificate_issued_at = datetime.datetime(2026, 8, 20,
                                                      tzinfo=datetime.timezone.utc)
        app.expires_at = datetime.date(2031, 8, 20)
        app.save()
        generate_certificate_pdf(app)
        app.refresh_from_db()
        return app

    def _overflowing_words(self, app):
        with pdfplumber.open(app.certificate_file.path) as pdf:
            return [
                (wd['text'], wd['x0'] / mm, wd['x1'] / mm)
                for wd in pdf.pages[0].extract_words()
                if wd['x0'] < BORDER_L - 0.5 or wd['x1'] > BORDER_R + 0.5
            ]

    def test_an_ordinary_certificate_stays_inside_the_border(self):
        app = self._render('Glory', 'Ibeju-Lego/000103', ('Test', 'Glory'))
        self.assertEqual(self._overflowing_words(app), [])

    def test_the_valid_until_column_stays_inside_the_border(self):
        """The specific failure: the last column sat hard against the page edge."""
        app = self._render('Glory', 'Ibeju-Lego/000103', ('Test', 'Glory'))
        with pdfplumber.open(app.certificate_file.path) as pdf:
            words = pdf.pages[0].extract_words()
        until = [wd for wd in words if wd['text'] in ('UNTIL', '2031')]
        self.assertTrue(until, 'the expiry column must be on the certificate')
        for wd in until:
            self.assertLessEqual(wd['x1'], BORDER_R, f"{wd['text']} crosses the border")

    def test_long_names_and_localities_still_fit(self):
        app = self._render(
            'Alhaji Sheik Rabiu Adebayo Memorial Boulevard Extension',
            'Oke-Odo/Elemoro Community Layout Phase II',
            ('Oluwafunmilayo', 'Adebanjo-Ogunsanya'))
        self.assertEqual(self._overflowing_words(app), [])
