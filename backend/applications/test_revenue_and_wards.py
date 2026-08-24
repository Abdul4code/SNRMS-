"""Revenue split by kind of work, and the ward the applicant no longer supplies."""
import datetime
import uuid

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from applications.revenue import NEW_STREET, RENEWAL, VALIDATION, revenue_breakdown
from applications.wards import resolve_ward, ward_for_locality
from config.models import BuildingSurvey, StreetType
from payments.models import Payment, PaymentStage, PaymentStatus


def confirmed(app, stage, amount, when):
    return Payment.objects.create(
        application=app, stage=stage, amount_expected=amount, amount_submitted=amount,
        status=PaymentStatus.CONFIRMED, confirmed_at=when)


class RevenueBreakdownTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='rev@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.when = timezone.now()
        self.start = self.when - datetime.timedelta(days=1)
        self.end = self.when + datetime.timedelta(days=1)

    def app(self, is_legacy):
        return Application.objects.create(
            applicant=self.user, proposed_street_name='X', location_description='d',
            street_type=self.st, is_legacy=is_legacy,
            status=ApplicationStatus.CERTIFICATE_ISSUED)

    def test_a_validation_fee_is_not_counted_as_a_new_street(self):
        """A validation pays the ordinary application fee too, so the stage alone
        cannot tell the two apart — the kind of application decides."""
        confirmed(self.app(False), PaymentStage.STAGE_A, 210000, self.when)
        confirmed(self.app(True), PaymentStage.STAGE_A, 125, self.when)
        out = revenue_breakdown(self.start, self.end)
        self.assertEqual(out['categories'][NEW_STREET]['total'], 210000)
        self.assertEqual(out['categories'][VALIDATION]['total'], 125)

    def test_the_revalidation_fee_is_counted_at_last(self):
        """It was missing from the audit entirely, so validation money vanished."""
        legacy = self.app(True)
        confirmed(legacy, PaymentStage.STAGE_A, 100, self.when)
        confirmed(legacy, PaymentStage.REVALIDATION, 900, self.when)
        out = revenue_breakdown(self.start, self.end)
        self.assertEqual(out['categories'][VALIDATION]['total'], 1000)
        self.assertEqual(out['total'], 1000, 'revalidation must reach the grand total')

    def test_renewals_stand_on_their_own(self):
        confirmed(self.app(False), PaymentStage.RENEWAL, 5000, self.when)
        out = revenue_breakdown(self.start, self.end)
        self.assertEqual(out['categories'][RENEWAL]['total'], 5000)
        self.assertEqual(out['categories'][NEW_STREET]['total'], 0,
                         'a renewal is a renewal even on a new-name application')

    def test_each_category_breaks_down_by_fee(self):
        new = self.app(False)
        confirmed(new, PaymentStage.STAGE_A, 210000, self.when)
        confirmed(new, PaymentStage.STAGE_C, 2000000, self.when)
        fees = revenue_breakdown(self.start, self.end)['categories'][NEW_STREET]['fees']
        self.assertEqual(fees[PaymentStage.STAGE_A]['total'], 210000)
        self.assertEqual(fees[PaymentStage.STAGE_C]['total'], 2000000)

    def test_the_three_categories_add_up_to_the_total(self):
        confirmed(self.app(False), PaymentStage.STAGE_A, 100, self.when)
        confirmed(self.app(True), PaymentStage.REVALIDATION, 200, self.when)
        confirmed(self.app(False), PaymentStage.RENEWAL, 300, self.when)
        out = revenue_breakdown(self.start, self.end)
        self.assertEqual(sum(b['total'] for b in out['categories'].values()), out['total'])
        self.assertEqual(out['total'], 600)

    def test_one_category_can_be_asked_for_alone(self):
        confirmed(self.app(False), PaymentStage.STAGE_A, 100, self.when)
        confirmed(self.app(True), PaymentStage.STAGE_A, 200, self.when)
        out = revenue_breakdown(self.start, self.end, VALIDATION)
        self.assertEqual(list(out['categories']), [VALIDATION])
        self.assertEqual(out['total'], 200)

    def test_money_outside_the_period_is_left_out(self):
        confirmed(self.app(False), PaymentStage.STAGE_A, 100,
                  self.when - datetime.timedelta(days=30))
        self.assertEqual(revenue_breakdown(self.start, self.end)['total'], 0)

    def test_unconfirmed_money_is_not_revenue(self):
        Payment.objects.create(
            application=self.app(False), stage=PaymentStage.STAGE_A,
            amount_expected=100, amount_submitted=100, status=PaymentStatus.SUBMITTED)
        self.assertEqual(revenue_breakdown(self.start, self.end)['total'], 0)


class AuditEndpointTests(TestCase):
    def setUp(self):
        self.chairman = User.objects.create_user(
            email='chair@example.com', password='x', first_name='C', last_name='H',
            role=Role.COMMITTEE_CHAIRMAN)
        self.user = User.objects.create_user(
            email='ap@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')
        now = timezone.now()
        for legacy, stage, amount in ((False, PaymentStage.STAGE_A, 210000),
                                      (True, PaymentStage.REVALIDATION, 900),
                                      (False, PaymentStage.RENEWAL, 5000)):
            app = Application.objects.create(
                applicant=self.user, proposed_street_name='X', location_description='d',
                street_type=self.st, is_legacy=legacy,
                status=ApplicationStatus.CERTIFICATE_ISSUED)
            confirmed(app, stage, amount, now)
        self.client = APIClient()
        self.client.force_authenticate(self.chairman)

    def test_the_chairman_sees_every_category_at_once(self):
        r = self.client.get('/api/applications/audit/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        cats = r.data['revenue_by_category']
        self.assertEqual(cats[NEW_STREET]['total'], 210000)
        self.assertEqual(cats[VALIDATION]['total'], 900)
        self.assertEqual(cats[RENEWAL]['total'], 5000)
        self.assertEqual(r.data['total_revenue'], 215900)

    def test_the_chairman_can_filter_to_one_category(self):
        r = self.client.get('/api/applications/audit/?category=validation')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.data['revenue_by_category']), [VALIDATION])
        self.assertEqual(r.data['total_revenue'], 900)
        self.assertEqual(r.data['category_label'], 'Validations of existing streets')

    def test_a_nonsense_category_falls_back_to_everything(self):
        r = self.client.get('/api/applications/audit/?category=nonsense')
        self.assertEqual(r.data['total_revenue'], 215900)

    def test_the_pdf_report_downloads_for_a_category(self):
        r = self.client.get('/api/applications/audit/report/?category=validation')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')


class WardResolutionTests(TestCase):
    """The applicant is no longer asked for a ward, so deriving it must be right."""

    def test_an_official_community_maps_to_its_ward(self):
        self.assertEqual(ward_for_locality('Abijo'), ward_for_locality('abijo'))
        self.assertTrue(ward_for_locality('Abijo'))

    def test_a_community_with_a_qualifier_still_maps(self):
        self.assertEqual(ward_for_locality('Abijo GRA'), ward_for_locality('Abijo'))
        self.assertEqual(ward_for_locality('Awoyaya Town'), ward_for_locality('Awoyaya'))

    def test_an_unknown_locality_falls_back_to_the_survey(self):
        BuildingSurvey.objects.create(
            kobo_id=1, kobo_uuid=uuid.uuid4(), locality='Nowhere Estate', ward='E',
            latitude='6.4700000', longitude='3.6600000')
        self.assertEqual(ward_for_locality('Nowhere Estate'), '')
        self.assertEqual(resolve_ward('Nowhere Estate'), 'ward_e',
                         'the ward letter the enumerators recorded should settle it')

    def test_the_map_location_settles_it_when_the_name_cannot(self):
        BuildingSurvey.objects.create(
            kobo_id=2, kobo_uuid=uuid.uuid4(), locality='Somewhere', ward='Ward F',
            latitude='6.4700000', longitude='3.6600000')
        self.assertEqual(resolve_ward('Unlisted Layout', 6.47001, 3.66001), 'ward_f')

    def test_nothing_known_returns_the_fallback_untouched(self):
        self.assertEqual(resolve_ward('Unlisted Layout', fallback='ward_a'), 'ward_a')


class ApplicationWardTests(TestCase):
    """The ward stored is the one derived, not the one the form happened to send."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='w@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        StreetType.objects.create(name='Street', code='ST')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_the_ward_comes_from_the_locality_not_the_form(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Test', 'location_description': '6.47,3.66',
            'locality': 'Abijo', 'ward': 'ward_a',      # deliberately wrong
            'latitude': '6.4700000', 'longitude': '3.6600000',
            'street_type': str(StreetType.objects.first().id),
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        app = Application.objects.get(pk=r.data['id'])
        self.assertEqual(app.ward, ward_for_locality('Abijo'))
