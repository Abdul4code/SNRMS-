"""Renewing an expired registration.

The same road as a validation — the committee looks at it, the Chairman decides —
but it renews a grant the council already made rather than bringing a new street
onto the register, it pays the renewal fee instead of the processing fee, and it
is counted on its own so the council can see what renewals are worth.
"""
import datetime

from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from applications.revenue import NEW_STREET, RENEWAL, VALIDATION, revenue_breakdown
from config.models import FeeConfiguration, FeeComponent, RenewalSettings, StreetType
from payments.models import Payment, PaymentStage, PaymentStatus
from payments.services import confirm_renewal_payment, confirm_stage_a_payment


class RenewExpiredWorkflowTests(TestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email='renew@example.com', password='x', first_name='R', last_name='E',
            role=Role.APPLICANT)
        self.finance = User.objects.create_user(
            email='fin2@example.com', password='x', first_name='F', last_name='N',
            role=Role.FINANCE)
        self.st = StreetType.objects.create(name='Street', code='ST')
        # The street-name fee the renewal fee is a share of, and the processing
        # fee a new application opens with.
        FeeConfiguration.objects.create(
            component=FeeComponent.STREET_NAME_FEE, street_type=self.st,
            amount=500000, is_active=True)
        FeeConfiguration.objects.create(
            component=FeeComponent.APPLICATION_FEE, amount=210000, is_active=True)
        self.client = APIClient()
        self.client.force_authenticate(self.applicant)

    def submit_renewal(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Akili', 'location_description': '6.47,3.66',
            'locality': 'Abijo', 'latitude': '6.4700000', 'longitude': '3.6600000',
            'street_type': str(self.st.id), 'is_renewal_request': 'true',
            'legacy_certificate': ContentFile(b'%PDF expired certificate', name='old.pdf'),
        }, format='multipart')
        self.assertEqual(r.status_code, 201, r.content[:300])
        return Application.objects.get(pk=r.data['id'])

    # --- what it is -------------------------------------------------------
    def test_a_renewal_is_marked_as_one_and_is_not_a_validation(self):
        app = self.submit_renewal()
        self.assertTrue(app.is_renewal_request)
        self.assertFalse(app.is_legacy, 'a renewal is its own kind, not a validation')

    def test_the_expired_certificate_is_required(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Akili', 'location_description': 'd',
            'locality': 'Abijo', 'street_type': str(self.st.id),
            'is_renewal_request': 'true',
        }, format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertIn('legacy_certificate', r.data)

    def test_it_cannot_be_a_validation_and_a_renewal_at_once(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Akili', 'location_description': 'd',
            'locality': 'Abijo', 'street_type': str(self.st.id),
            'is_renewal_request': 'true', 'is_legacy': 'true',
            'legacy_certificate': ContentFile(b'x', name='old.pdf'),
        }, format='multipart')
        self.assertEqual(r.status_code, 400)

    # --- what it costs ----------------------------------------------------
    def test_it_opens_with_the_renewal_fee_not_the_processing_fee(self):
        app = self.submit_renewal()
        r = self.client.post(f'/api/applications/{app.id}/request-payment/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        payment = Payment.objects.get(application=app)
        self.assertEqual(payment.stage, PaymentStage.RENEWAL)
        self.assertLess(payment.amount_expected, 210000,
                        'the renewal fee is a fraction of the street-name fee')
        self.assertGreater(payment.amount_expected, 0)

    def test_a_new_application_still_opens_with_the_processing_fee(self):
        from documents.models import Document, DocumentType
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Brand New', 'location_description': 'd',
            'locality': 'Abijo', 'street_type': str(self.st.id),
        }, format='json')
        app = Application.objects.get(pk=r.data['id'])
        # A new name needs its supporting documents; only the certificate-carrying
        # kinds are exempt.
        Document.objects.create(
            application=app, document_type=DocumentType.choices[0][0],
            file=ContentFile(b'x', name='doc.pdf'), original_filename='doc.pdf',
            file_size=1, mime_type='application/pdf', uploaded_by=self.applicant)
        r = self.client.post(f'/api/applications/{app.id}/request-payment/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(Payment.objects.get(application=app).stage, PaymentStage.STAGE_A)

    # --- where it goes ----------------------------------------------------
    def test_paying_sends_it_to_the_committee_like_a_validation(self):
        """It must not be renewed on the spot: nobody has looked at it yet."""
        app = self.submit_renewal()
        self.client.post(f'/api/applications/{app.id}/request-payment/')
        payment = Payment.objects.get(application=app)
        payment.status = PaymentStatus.SUBMITTED
        payment.save()
        app.refresh_from_db()
        app.transition_to(ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION,
                          actor=self.applicant, remarks='')
        confirm_renewal_payment(payment, self.finance)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)

    def test_renewing_a_certificate_this_system_issued_is_unchanged(self):
        """The one-click renewal still renews on the spot."""
        RenewalSettings.get()
        app = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Old', location_description='d',
            street_type=self.st, status=ApplicationStatus.CERTIFICATE_ISSUED,
            expires_at=datetime.date.today() + datetime.timedelta(days=10))
        r = self.client.post(f'/api/applications/{app.id}/renew/')
        self.assertEqual(r.status_code, 200, r.content[:300])
        payment = Payment.objects.get(application=app, stage=PaymentStage.RENEWAL)
        app.refresh_from_db()
        app.transition_to(ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION,
                          actor=self.applicant, remarks='')
        confirm_renewal_payment(payment, self.finance)
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.RENEWED)

    # --- how it is counted ------------------------------------------------
    def test_renewal_money_is_counted_as_a_renewal(self):
        app = self.submit_renewal()
        now = timezone.now()
        Payment.objects.create(application=app, stage=PaymentStage.RENEWAL,
                               amount_expected=25000, amount_submitted=25000,
                               status=PaymentStatus.CONFIRMED, confirmed_at=now)
        out = revenue_breakdown(now - datetime.timedelta(days=1),
                                now + datetime.timedelta(days=1))
        self.assertEqual(out['categories'][RENEWAL]['total'], 25000)
        self.assertEqual(out['categories'][NEW_STREET]['total'], 0)
        self.assertEqual(out['categories'][VALIDATION]['total'], 0)

    def test_a_renewal_does_not_leak_into_the_other_categories(self):
        """Even a fee that is not the renewal fee, on a renewal application."""
        app = self.submit_renewal()
        now = timezone.now()
        Payment.objects.create(application=app, stage=PaymentStage.STAGE_C,
                               amount_expected=500, amount_submitted=500,
                               status=PaymentStatus.CONFIRMED, confirmed_at=now)
        out = revenue_breakdown(now - datetime.timedelta(days=1),
                                now + datetime.timedelta(days=1))
        self.assertEqual(out['categories'][RENEWAL]['total'], 500)
        self.assertEqual(out['categories'][NEW_STREET]['total'], 0)


class RenewalAuditTests(TestCase):
    def setUp(self):
        self.chairman = User.objects.create_user(
            email='chair4@example.com', password='x', first_name='C', last_name='H',
            role=Role.COMMITTEE_CHAIRMAN)
        self.applicant = User.objects.create_user(
            email='ap2@example.com', password='x', first_name='A', last_name='P',
            role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')
        now = timezone.now()
        for kind, amount, stage in (
            ({'is_legacy': False}, 210000, PaymentStage.STAGE_A),
            ({'is_legacy': True}, 900, PaymentStage.REVALIDATION),
            ({'is_renewal_request': True}, 25000, PaymentStage.RENEWAL),
        ):
            app = Application.objects.create(
                applicant=self.applicant, proposed_street_name='X',
                location_description='d', street_type=self.st,
                status=ApplicationStatus.CERTIFICATE_ISSUED, **kind)
            Payment.objects.create(application=app, stage=stage, amount_expected=amount,
                                   amount_submitted=amount,
                                   status=PaymentStatus.CONFIRMED, confirmed_at=now)
        self.client = APIClient()
        self.client.force_authenticate(self.chairman)

    def test_the_audit_shows_renewals_on_their_own(self):
        r = self.client.get('/api/applications/audit/?from=2000-01-01&to=2100-01-01')
        cats = r.data['revenue_by_category']
        self.assertEqual(cats[NEW_STREET]['total'], 210000)
        self.assertEqual(cats[VALIDATION]['total'], 900)
        self.assertEqual(cats[RENEWAL]['total'], 25000)

    def test_the_chairman_can_filter_to_renewals(self):
        r = self.client.get('/api/applications/audit/?category=renewal&from=2000-01-01&to=2100-01-01')
        self.assertEqual(list(r.data['revenue_by_category']), [RENEWAL])
        self.assertEqual(r.data['total_revenue'], 25000)
        self.assertEqual(r.data['total_applications'], 1, 'one renewal application')

    def test_filtering_to_new_streets_excludes_the_renewal(self):
        r = self.client.get('/api/applications/audit/?category=new_street&from=2000-01-01&to=2100-01-01')
        self.assertEqual(r.data['total_applications'], 1)
        self.assertEqual(r.data['total_revenue'], 210000)
