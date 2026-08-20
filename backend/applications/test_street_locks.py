"""Exercise the street-hold rules end to end against a real (test) database."""
import datetime

from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from applications.street_locks import (
    applications_at_location, lock_state, street_holder,
)
from config.models import StreetType
from payments.models import Payment, PaymentStage, PaymentStatus

LAT, LNG = 6.4700000, 3.6600000
FAR_LAT, FAR_LNG = 6.5000000, 3.8000000       # ~15 km away — a different street
NEAR_LAT, NEAR_LNG = 6.4700400, 3.6600000     # ~44 m away — same street


def mk_user(email):
    return User.objects.create_user(email=email, password='x', first_name='A',
                                    last_name='B', role=Role.APPLICANT)


class StreetHoldTests(TestCase):
    def setUp(self):
        self.u1 = mk_user('one@example.com')
        self.u2 = mk_user('two@example.com')
        self.st = StreetType.objects.create(name='Street', code='ST')

    def mk_app(self, user, status, lat=LAT, lng=LNG, age_days=0):
        a = Application.objects.create(
            applicant=user, proposed_street_name='Test', location_description='d',
            street_type=self.st, latitude=lat, longitude=lng, status=status)
        if age_days:
            when = timezone.now() - datetime.timedelta(days=age_days)
            Application.objects.filter(pk=a.pk).update(created_at=when, updated_at=when)
            a.refresh_from_db()
        return a

    def pay(self, app, days_ago=0, confirmed=True):
        when = timezone.now() - datetime.timedelta(days=days_ago)
        return Payment.objects.create(
            application=app, stage=PaymentStage.STAGE_A, amount_expected=1000,
            status=PaymentStatus.CONFIRMED if confirmed else PaymentStatus.SUBMITTED,
            confirmed_at=when if confirmed else None, submitted_at=when)

    # --- rule 1: unpaid gets 3 days ------------------------------------------
    def test_unpaid_holds_for_three_days(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT, age_days=1)
        st = lock_state(a)
        self.assertTrue(st['holds'])
        self.assertEqual(st['kind'], 'unpaid')
        self.assertIsNotNone(street_holder(LAT, LNG))

    def test_unpaid_lapses_after_three_days(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT, age_days=4)
        self.assertFalse(lock_state(a)['holds'])
        self.assertIsNone(street_holder(LAT, LNG), 'street must reopen after 3 unpaid days')

    def test_unpaid_lapse_is_exactly_three_days(self):
        just_inside = self.mk_app(self.u1, ApplicationStatus.SUBMITTED, age_days=2)
        self.assertTrue(lock_state(just_inside)['holds'])
        just_outside = self.mk_app(self.u2, ApplicationStatus.SUBMITTED,
                                   lat=FAR_LAT, lng=FAR_LNG, age_days=3)
        self.assertFalse(lock_state(just_outside)['holds'])

    # --- rule 2: paid holds for a month --------------------------------------
    def test_paid_holds_for_one_month(self):
        a = self.mk_app(self.u1, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW, age_days=20)
        self.pay(a, days_ago=20)
        st = lock_state(a)
        self.assertTrue(st['holds'])
        self.assertEqual(st['kind'], 'decision')
        self.assertIsNotNone(street_holder(LAT, LNG))

    def test_paid_survives_the_three_day_unpaid_window(self):
        """Paying must reset the clock — 5 days old but paid is still held."""
        a = self.mk_app(self.u1, ApplicationStatus.STAGE_A_CONFIRMED, age_days=5)
        self.pay(a, days_ago=4)
        self.assertTrue(lock_state(a)['holds'])

    def test_paid_lapses_after_one_month(self):
        a = self.mk_app(self.u1, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW, age_days=40)
        self.pay(a, days_ago=31)
        self.assertFalse(lock_state(a)['holds'])
        self.assertIsNone(street_holder(LAT, LNG), 'street must reopen a month after payment')

    def test_month_runs_from_payment_not_from_application(self):
        a = self.mk_app(self.u1, ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW, age_days=40)
        self.pay(a, days_ago=10)
        self.assertTrue(lock_state(a)['holds'], 'clock starts at payment, not application')

    def test_unconfirmed_payment_still_counts(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION,
                        age_days=5)
        self.pay(a, days_ago=4, confirmed=False)
        self.assertTrue(lock_state(a)['holds'],
                        'applicant must not lose the street waiting on Finance')

    def test_rejected_payment_is_not_payment(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT, age_days=5)
        p = self.pay(a, days_ago=4)
        p.status = PaymentStatus.REJECTED
        p.save()
        self.assertFalse(lock_state(a)['holds'])

    # --- rule 3: reopened streets collect applications -----------------------
    def test_second_applicant_may_apply_once_hold_lapses(self):
        first = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT, age_days=5)
        self.assertIsNone(street_holder(LAT, LNG))
        second = self.mk_app(self.u2, ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
                             lat=NEAR_LAT, lng=NEAR_LNG)
        contention = applications_at_location(second)
        self.assertIsNotNone(contention)
        self.assertEqual(contention['position'], 2, 'newcomer is the 2nd for this street')
        self.assertEqual(contention['total'], 2)
        self.assertEqual(contention['others'][0]['id'], str(first.pk))
        self.assertFalse(contention['others'][0]['holds_street'])

    def test_first_applicant_sees_it_is_now_contested(self):
        first = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT, age_days=5)
        self.mk_app(self.u2, ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
                    lat=NEAR_LAT, lng=NEAR_LNG)
        self.assertEqual(applications_at_location(first)['position'], 1)

    def test_a_lone_application_is_not_contested(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT)
        self.assertIsNone(applications_at_location(a))

    def test_different_street_is_not_contention(self):
        self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT)
        other = self.mk_app(self.u2, ApplicationStatus.AWAITING_STAGE_A_PAYMENT,
                            lat=FAR_LAT, lng=FAR_LNG)
        self.assertIsNone(applications_at_location(other))

    # --- a granted name never returns to the pool ----------------------------
    def test_issued_certificate_holds_forever(self):
        a = self.mk_app(self.u1, ApplicationStatus.CERTIFICATE_ISSUED, age_days=400)
        st = lock_state(a)
        self.assertTrue(st['holds'])
        self.assertEqual(st['kind'], 'settled')
        self.assertIsNone(st['expires_at'])
        self.assertIsNotNone(street_holder(LAT, LNG))

    def test_rejected_application_releases_the_street(self):
        self.mk_app(self.u1, ApplicationStatus.REJECTED_BY_CHAIRMAN)
        self.assertIsNone(street_holder(LAT, LNG))

    def test_withdrawn_application_releases_the_street(self):
        self.mk_app(self.u1, ApplicationStatus.WITHDRAWN)
        self.assertIsNone(street_holder(LAT, LNG))

    def test_legacy_application_never_holds(self):
        a = self.mk_app(self.u1, ApplicationStatus.AWAITING_STAGE_A_PAYMENT)
        a.is_legacy = True
        a.save()
        self.assertFalse(lock_state(a)['holds'])
        self.assertIsNone(street_holder(LAT, LNG))

    # --- proximity ------------------------------------------------------------
    def test_hold_covers_the_same_street_not_the_next_one(self):
        self.mk_app(self.u1, ApplicationStatus.STAGE_A_CONFIRMED)
        self.assertIsNotNone(street_holder(NEAR_LAT, NEAR_LNG), '44 m away is the same street')
        self.assertIsNone(street_holder(FAR_LAT, FAR_LNG), '15 km away is not')


class HoldSerializationTests(TestCase):
    """The hold reaches the applicant; the rival list reaches only staff."""

    def setUp(self):
        self.applicant = mk_user('app@example.com')
        self.staff = User.objects.create_user(
            email='staff@example.com', password='x', first_name='S', last_name='T',
            role=Role.NAMING_COMMITTEE)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.a = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Test', location_description='d',
            street_type=self.st, latitude=LAT, longitude=LNG,
            status=ApplicationStatus.AWAITING_STAGE_A_PAYMENT)
        old = Application.objects.create(
            applicant=self.applicant, proposed_street_name='Older', location_description='d',
            street_type=self.st, latitude=NEAR_LAT, longitude=NEAR_LNG,
            status=ApplicationStatus.AWAITING_STAGE_A_PAYMENT)
        Application.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=10))

    def _data(self, user):
        from applications.serializers import ApplicationDetailSerializer

        class Req:
            pass
        req = Req()
        req.user = user
        return ApplicationDetailSerializer(self.a, context={'request': req}).data

    def test_applicant_is_told_to_pay_within_three_days(self):
        hold = self._data(self.applicant)['street_hold']
        self.assertTrue(hold['holds'])
        self.assertEqual(hold['kind'], 'unpaid')
        self.assertIn('3 day', hold['message'])

    def test_applicant_cannot_see_the_other_applications(self):
        self.assertIsNone(self._data(self.applicant)['location_contention'])

    def test_staff_see_the_queue_position(self):
        c = self._data(self.staff)['location_contention']
        self.assertEqual(c['position'], 2)
        self.assertEqual(c['total'], 2)
