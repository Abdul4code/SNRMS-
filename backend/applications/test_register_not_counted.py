"""The old paper register is history, not a queue of applications.

352 rows were imported from the council's paper register so their names would be
taken in the registry. They are not work anybody submitted, so counting them made
the dashboard read "352 applications, 352 approved" on a system nobody had
applied to. A validation somebody actually applies for is a different thing and
still counts.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from config.models import StreetType


class RegisterImportNotCountedTests(TestCase):
    def setUp(self):
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.importer = User.objects.create_user(
            email='legacy-registry@ibeju-lekki.gov.ng', password='x',
            first_name='Legacy', last_name='Registry', role=Role.APPLICANT)
        self.applicant = User.objects.create_user(
            email='real@example.com', password='x', first_name='R', last_name='A',
            role=Role.APPLICANT)
        self.chairman = User.objects.create_user(
            email='chair2@example.com', password='x', first_name='C', last_name='H',
            role=Role.COMMITTEE_CHAIRMAN)

        # A row from the old paper register.
        self.imported = Application.objects.create(
            applicant=self.importer, proposed_street_name='Old Street',
            location_description='d', street_type=self.st, is_legacy=True,
            is_register_import=True, status=ApplicationStatus.CERTIFICATE_ISSUED)
        # A validation somebody actually applied for.
        self.validation = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Real Validation',
            location_description='d', street_type=self.st, is_legacy=True,
            status=ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)

        self.client = APIClient()
        self.client.force_authenticate(self.chairman)

    def rows(self, response):
        data = response.data
        return data['results'] if isinstance(data, dict) else data

    def test_the_imported_register_is_not_in_the_application_list(self):
        rows = self.rows(self.client.get('/api/applications/'))
        names = [r['proposed_street_name'] for r in rows]
        self.assertNotIn('Old Street', names)

    def test_a_validation_someone_applied_for_still_counts(self):
        rows = self.rows(self.client.get('/api/applications/'))
        self.assertIn('Real Validation', [r['proposed_street_name'] for r in rows],
                      'a validation is real work and must not be swept up with the register')

    def test_the_register_can_still_be_asked_for_explicitly(self):
        rows = self.rows(self.client.get('/api/applications/?include_register=true'))
        self.assertIn('Old Street', [r['proposed_street_name'] for r in rows])

    def test_the_audit_does_not_count_the_register(self):
        r = self.client.get('/api/applications/audit/?from=2000-01-01&to=2100-01-01')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.data['total_applications'], 1,
                         'only the validation somebody applied for')

    def test_the_audit_does_not_count_register_certificates(self):
        r = self.client.get('/api/applications/audit/?from=2000-01-01&to=2100-01-01')
        self.assertEqual(r.data['certificates_issued'], 0,
                         'importing the old register did not issue a certificate')

    def test_an_applicant_still_sees_their_own_validation(self):
        self.client.force_authenticate(self.applicant)
        rows = self.rows(self.client.get('/api/applications/'))
        self.assertEqual([r['proposed_street_name'] for r in rows], ['Real Validation'])


class RegistryStatusLabelTests(TestCase):
    """In the applications database, an imported row says what it is."""

    def setUp(self):
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.importer = User.objects.create_user(
            email='legacy-registry@ibeju-lekki.gov.ng', password='x',
            first_name='Legacy', last_name='Registry', role=Role.APPLICANT)
        self.applicant = User.objects.create_user(
            email='someone@example.com', password='x', first_name='S', last_name='O',
            role=Role.APPLICANT)
        self.chairman = User.objects.create_user(
            email='chair3@example.com', password='x', first_name='C', last_name='H',
            role=Role.COMMITTEE_CHAIRMAN)
        self.client = APIClient()
        self.client.force_authenticate(self.chairman)

    def row_for(self, name):
        r = self.client.get('/api/applications/registry/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        return next(x for x in r.data['results'] if x['proposed_street_name'] == name)

    def test_an_imported_register_row_reads_as_legacy(self):
        Application.objects.create(
            applicant=self.importer, proposed_street_name='Imported Street',
            location_description='d', street_type=self.st, is_legacy=True,
            is_register_import=True, status=ApplicationStatus.CERTIFICATE_ISSUED)
        row = self.row_for('Imported Street')
        self.assertEqual(row['status_display'], 'Legacy')
        self.assertTrue(row['is_register_import'])

    def test_a_certificate_this_system_issued_still_says_so(self):
        """A validation that ran the full course earned its certificate."""
        Application.objects.create(
            applicant=self.applicant, proposed_street_name='Earned Street',
            location_description='d', street_type=self.st, is_legacy=True,
            status=ApplicationStatus.CERTIFICATE_ISSUED)
        row = self.row_for('Earned Street')
        self.assertEqual(row['status_display'], 'Certificate Issued')
        self.assertFalse(row['is_register_import'])

    def test_an_ordinary_application_reads_normally(self):
        Application.objects.create(
            applicant=self.applicant, proposed_street_name='New Street',
            location_description='d', street_type=self.st,
            status=ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)
        self.assertEqual(self.row_for('New Street')['status_display'],
                         'Under Naming Committee Review')

    def test_the_raw_status_is_still_there_for_anything_that_needs_it(self):
        Application.objects.create(
            applicant=self.importer, proposed_street_name='Imported Two',
            location_description='d', street_type=self.st, is_legacy=True,
            is_register_import=True, status=ApplicationStatus.CERTIFICATE_ISSUED)
        self.assertEqual(self.row_for('Imported Two')['status'], 'certificate_issued')
