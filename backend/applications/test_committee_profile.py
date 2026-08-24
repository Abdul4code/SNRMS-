"""A committee member maintains their own name, office and PIN.

Nobody else can rename them, and nobody — not even whoever set the system up —
needs to know their PIN. The PIN is what signs a recommendation to the Chairman,
so it matters that it belongs to one person.
"""
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import CommitteeMember

PROFILE = '/api/applications/committee/profile/'


class MemberProfileTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email='cm@example.com', password='x', first_name='C', last_name='M',
            role=Role.NAMING_COMMITTEE)
        self.me = CommitteeMember.objects.create(
            number=2, name='Committee Member 2', pin_hash=make_password('2222'))
        self.other = CommitteeMember.objects.create(
            number=3, name='Committee Member 3', pin_hash=make_password('3333'))
        self.client = APIClient()
        self.client.force_authenticate(self.staff)
        self.token = self.client.post('/api/applications/committee/verify-member/',
                                      {'number': 2, 'pin': '2222'}, format='json').data['token']

    def hdr(self, token=None):
        return {'HTTP_X_COMMITTEE_MEMBER': token or self.token}

    def patch(self, data, token=None):
        return self.client.patch(PROFILE, data, format='json', **self.hdr(token))

    # --- name and office --------------------------------------------------
    def test_a_member_can_set_their_own_name_and_office(self):
        r = self.patch({'name': 'Dr Adekoya Augustine A.', 'title': 'Secretary'})
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.me.refresh_from_db()
        self.assertEqual(self.me.name, 'Dr Adekoya Augustine A.')
        self.assertEqual(self.me.title, 'Secretary')

    def test_editing_touches_only_the_member_who_asked(self):
        self.patch({'name': 'Someone Else'})
        self.other.refresh_from_db()
        self.assertEqual(self.other.name, 'Committee Member 3')

    def test_a_scrap_of_a_name_is_refused(self):
        self.assertEqual(self.patch({'name': 'A'}).status_code, 400)

    # --- the PIN ----------------------------------------------------------
    def test_a_member_can_change_their_pin(self):
        r = self.patch({'current_pin': '2222', 'new_pin': '8473'})
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.me.refresh_from_db()
        self.assertTrue(self.me.check_pin('8473'))
        self.assertFalse(self.me.check_pin('2222'))

    def test_the_current_pin_is_required_to_change_it(self):
        """A console left open must not be enough to lock the member out."""
        r = self.patch({'current_pin': '0000', 'new_pin': '8473'})
        self.assertEqual(r.status_code, 400)
        self.me.refresh_from_db()
        self.assertTrue(self.me.check_pin('2222'), 'the old PIN must still work')

    def test_the_shipped_default_is_refused(self):
        r = self.patch({'current_pin': '2222', 'new_pin': '2222'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('default', r.data['detail'].lower())

    def test_four_of_the_same_digit_is_refused(self):
        self.assertEqual(self.patch({'current_pin': '2222', 'new_pin': '9999'}).status_code, 400)

    def test_an_obvious_run_of_digits_is_refused(self):
        self.assertEqual(self.patch({'current_pin': '2222', 'new_pin': '1234'}).status_code, 400)

    def test_a_short_pin_is_refused(self):
        self.assertEqual(self.patch({'current_pin': '2222', 'new_pin': '12'}).status_code, 400)

    def test_letters_are_not_a_pin(self):
        self.assertEqual(self.patch({'current_pin': '2222', 'new_pin': 'abcd'}).status_code, 400)

    # --- who may do this --------------------------------------------------
    def test_without_a_member_token_nothing_can_be_changed(self):
        r = self.client.patch(PROFILE, {'name': 'Nobody'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.me.refresh_from_db()
        self.assertEqual(self.me.name, 'Committee Member 2')

    def test_a_forged_token_is_refused(self):
        r = self.patch({'name': 'Nobody'}, token='not-a-real-token')
        self.assertEqual(r.status_code, 403)

    # --- the nudge --------------------------------------------------------
    def test_the_console_is_told_when_the_pin_is_still_the_default(self):
        r = self.client.get(PROFILE, **self.hdr())
        self.assertTrue(r.data['using_default_pin'])
        self.patch({'current_pin': '2222', 'new_pin': '8473'})
        r = self.client.get(PROFILE, **self.hdr())
        self.assertFalse(r.data['using_default_pin'])
