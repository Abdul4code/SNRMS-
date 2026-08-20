"""A validate-existing-street application must go through committee review
exactly like a new one. It reached the committee's screen and broke there.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from config.models import StreetType
from payments.models import Payment, PaymentStage, PaymentStatus
from payments.services import confirm_stage_a_payment

LAT, LNG = 6.4700000, 3.6600000


class LegacyCommitteeReviewTests(TestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(
            email='a@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.finance = User.objects.create_user(
            email='f@example.com', password='x', first_name='F', last_name='N',
            role=Role.FINANCE)
        self.committee = User.objects.create_user(
            email='c@example.com', password='x', first_name='C', last_name='M',
            role=Role.NAMING_COMMITTEE)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.client = APIClient()

    def _application(self, is_legacy):
        """An application sitting where Finance leaves it: fee confirmed."""
        app = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Akili',
            location_description='6.470000,3.660000', street_type=self.st,
            latitude=LAT, longitude=LNG, is_legacy=is_legacy,
            status=ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION)
        payment = Payment.objects.create(
            application=app, stage=PaymentStage.STAGE_A, amount_expected=1000,
            status=PaymentStatus.SUBMITTED)
        confirm_stage_a_payment(payment, self.finance)
        app.refresh_from_db()
        return app

    def test_finance_confirmation_sends_a_legacy_application_to_the_committee(self):
        app = self._application(is_legacy=True)
        self.assertEqual(app.status, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)

    def test_committee_can_open_a_legacy_application(self):
        """The detail screen the committee opens must render for legacy too."""
        app = self._application(is_legacy=True)
        self.client.force_authenticate(self.committee)
        r = self.client.get(f'/api/applications/{app.id}/')
        self.assertEqual(r.status_code, 200, r.content[:400])

    def test_committee_sees_a_legacy_application_in_its_queue(self):
        legacy = self._application(is_legacy=True)
        self.client.force_authenticate(self.committee)
        r = self.client.get('/api/applications/?status=under_naming_committee_review')
        self.assertEqual(r.status_code, 200, r.content[:400])
        rows = r.data['results'] if isinstance(r.data, dict) else r.data
        self.assertIn(str(legacy.id), [str(x['id']) for x in rows])

    def test_committee_review_screen_loads_for_a_legacy_application(self):
        app = self._application(is_legacy=True)
        self.client.force_authenticate(self.committee)
        r = self.client.get(f'/api/applications/committee/{app.id}/review/')
        self.assertEqual(r.status_code, 200, r.content[:400])

    def test_committee_can_approve_a_legacy_application(self):
        app = self._application(is_legacy=True)
        self.client.force_authenticate(self.committee)
        r = self.client.post(f'/api/applications/{app.id}/committee-review/',
                             {'decision': 'approved', 'remarks': 'ok'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:400])
        app.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL)

    def test_a_new_application_behaves_the_same_way(self):
        """The control: this is the path the council says already works."""
        app = self._application(is_legacy=False)
        self.assertEqual(app.status, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)
        self.client.force_authenticate(self.committee)
        self.assertEqual(
            self.client.get(f'/api/applications/committee/{app.id}/review/').status_code, 200)


class LegacyCommitteeWorkflowTests(TestCase):
    """The whole committee round on a validate application: open it, mark the
    submissions reviewed, comment, reach quorum, forward to the LG Chairman.
    """

    def setUp(self):
        from django.contrib.auth.hashers import make_password
        from applications.models import CommitteeMember

        self.applicant = User.objects.create_user(
            email='a2@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.finance = User.objects.create_user(
            email='f2@example.com', password='x', first_name='F', last_name='N',
            role=Role.FINANCE)
        self.committee = User.objects.create_user(
            email='c2@example.com', password='x', first_name='C', last_name='M',
            role=Role.NAMING_COMMITTEE)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.members = [
            CommitteeMember.objects.create(number=n, name=f'Member {n}',
                                           pin_hash=make_password('1234'))
            for n in range(1, 5)   # 1 is the chairman; quorum needs 3 others
        ]
        self.client = APIClient()
        self.client.force_authenticate(self.committee)

        self.app = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Akili',
            location_description='6.470926,3.662995', street_type=self.st,
            latitude=LAT, longitude=LNG, is_legacy=True,
            status=ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION)
        payment = Payment.objects.create(
            application=self.app, stage=PaymentStage.STAGE_A, amount_expected=1000,
            status=PaymentStatus.SUBMITTED)
        confirm_stage_a_payment(payment, self.finance)
        self.app.refresh_from_db()

    def _token(self, number):
        r = self.client.post('/api/applications/committee/verify-member/',
                             {'number': number, 'pin': '1234'}, format='json')
        self.assertEqual(r.status_code, 200, r.content[:300])
        return r.data['token']

    def test_a_member_can_run_the_full_review_on_a_legacy_application(self):
        token = self._token(2)
        hdr = {'HTTP_X_COMMITTEE_MEMBER': token}

        # The legacy certificate must reach the committee — this is the document
        # they are reviewing, and it is not a Document record.
        r = self.client.get(f'/api/applications/committee/{self.app.id}/review/', **hdr)
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertTrue(r.data['is_legacy'])

        r = self.client.post(f'/api/applications/committee/{self.app.id}/mark-viewed/', **hdr)
        self.assertIn(r.status_code, (200, 201), r.content[:300])

        r = self.client.post(f'/api/applications/committee/{self.app.id}/comment/',
                             {'comment': 'Looks genuine.', 'signature': 'M2',
                              'recommendation': 'recommend'}, format='json', **hdr)
        self.assertIn(r.status_code, (200, 201), r.content[:300])

    def test_quorum_and_forwarding_work_for_a_legacy_application(self):
        for n in (2, 3, 4):    # quorum counts non-chairman members only
            token = self._token(n)
            hdr = {'HTTP_X_COMMITTEE_MEMBER': token}
            self.client.post(f'/api/applications/committee/{self.app.id}/mark-viewed/', **hdr)
            self.client.post(f'/api/applications/committee/{self.app.id}/comment/',
                             {'comment': f'Member {n} agrees.', 'signature': f'M{n}',
                              'recommendation': 'recommend'}, format='json', **hdr)

        chair = {'HTTP_X_COMMITTEE_MEMBER': self._token(1)}
        r = self.client.get(f'/api/applications/committee/{self.app.id}/review/', **chair)
        self.assertTrue(r.data['quorum_met'], 'three non-chairman comments make quorum')

        r = self.client.post(f'/api/applications/committee/{self.app.id}/forward/',
                             {'overall_recommendation': 'Validate it.',
                              'general_comment_to_applicant': 'Approved by committee.',
                              'decision': 'recommend'}, format='json', **chair)
        self.assertIn(r.status_code, (200, 201), r.content[:300])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL,
                         'a validated street must reach the Chairman like any other')
