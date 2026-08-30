"""One name per place, across the survey, the register and what applicants type."""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.localities import (canonical_locality, is_official,
                                     official_communities)
from applications.models import Application
from applications.wards import ward_for_locality
from config.models import StreetType


class CanonicalLocalityTests(TestCase):
    def test_the_councils_own_spelling_is_kept(self):
        self.assertEqual(canonical_locality('Abijo'), 'Abijo')
        self.assertEqual(canonical_locality('abijo'), 'Abijo')

    def test_survey_spellings_fold_onto_the_community(self):
        for spelling, community in (('Ayeteju', 'Aiyeteju'),
                                    ('Shappatti', 'Shapati'),
                                    ('Gbogije', 'Bogije'),
                                    ('Lagassa', 'Lagasa'),
                                    ('Abidjan', 'Abijo')):
            self.assertEqual(canonical_locality(spelling), community, spelling)

    def test_a_qualifier_does_not_make_a_new_place(self):
        self.assertEqual(canonical_locality('Abijo GRA'), 'Abijo')
        self.assertEqual(canonical_locality('Awoyaya Town'), 'Awoyaya')

    def test_a_road_recorded_as_a_locality_lands_where_its_buildings_are(self):
        """"New Road" is not a place; its buildings sit in Gbetu."""
        self.assertEqual(canonical_locality('New Road'), 'Gbetu')

    def test_places_the_official_list_omits_are_kept_as_themselves(self):
        """Igbojia and Majek are real: 142 and 51 surveyed buildings."""
        self.assertEqual(canonical_locality('Igbojia'), 'Igbojia')
        self.assertEqual(canonical_locality('Igbojiya'), 'Igbojia')
        self.assertEqual(canonical_locality('Majek Abijo'), 'Majek')

    def test_an_unknown_locality_is_returned_untouched(self):
        """Never file somebody under a place they did not name."""
        self.assertEqual(canonical_locality('Somewhere Brand New'), 'Somewhere Brand New')
        self.assertFalse(is_official('Somewhere Brand New'))

    def test_the_list_offered_to_applicants_is_the_councils(self):
        names = official_communities()
        self.assertEqual(len(names), 112, '110 official communities plus Igbojia and Majek')
        self.assertIn('Abijo', names)
        self.assertNotIn('Ayeteju', names, 'a misspelling must never be offered')

    def test_folding_happens_before_the_ward_is_derived(self):
        """Ayeteju and Aiyeteju are one community and so one ward."""
        self.assertTrue(ward_for_locality('Aiyeteju'))
        self.assertEqual(ward_for_locality('Ayeteju'), ward_for_locality('Aiyeteju'))


class ApplicationLocalityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='loc@example.com', password='x', first_name='L', last_name='O',
            role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_an_application_stores_the_councils_name(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Test', 'location_description': 'd',
            'locality': 'Ayeteju', 'street_type': str(self.st.id),
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        app = Application.objects.get(pk=r.data['id'])
        self.assertEqual(app.locality, 'Aiyeteju')
        self.assertEqual(app.ward, ward_for_locality('Aiyeteju'))

    def test_the_picker_offers_only_council_names(self):
        r = self.client.get('/api/config/communities/')
        self.assertEqual(r.status_code, 200)
        names = [c['name'] for c in r.data]
        self.assertIn('Aiyeteju', names)
        self.assertNotIn('Ayeteju', names, 'a misspelling must never be offered')


class CommunityPickerTests(TestCase):
    """The picker is the council's whole list, with a position where one is known."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='pick@example.com', password='x', first_name='P', last_name='K',
            role=Role.APPLICANT)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_every_community_is_offered_not_just_the_surveyed_ones(self):
        r = self.client.get('/api/config/communities/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 112,
                         'the council names 110, plus Igbojia and Majek')
        names = [c['name'] for c in r.data]
        # A community the survey never reached must still be pickable.
        self.assertIn('Orofun', names)
        self.assertIn('Magbon-Alade', names)

    def test_each_entry_carries_its_ward(self):
        r = self.client.get('/api/config/communities/')
        abijo = next(c for c in r.data if c['name'] == 'Abijo')
        self.assertTrue(abijo['ward'], 'the ward is what the map falls back to')

    def test_a_position_is_null_rather_than_guessed(self):
        """Nobody has mapped every hamlet; an invented centre would be worse."""
        r = self.client.get('/api/config/communities/')
        for c in r.data:
            if c['latitude'] is None:
                self.assertIsNone(c['longitude'])
            else:
                self.assertTrue(6.3 <= c['latitude'] <= 6.6, c['name'])
                self.assertTrue(3.5 <= c['longitude'] <= 4.2, c['name'])

    def test_a_position_comes_from_real_evidence(self):
        """Survey buildings, an OSM place, or the geocoder — never a guess."""
        r = self.client.get('/api/config/communities/')
        placed = [c for c in r.data if c['latitude'] is not None]
        self.assertTrue(placed, 'some communities must be placeable')
        for c in placed:
            self.assertIn(c['position_from'], ('survey', 'osm', 'geocode'), c['name'])

    def test_a_surveyed_community_is_placed_by_its_own_buildings(self):
        r = self.client.get('/api/config/communities/')
        abijo = next(c for c in r.data if c['name'] == 'Abijo')
        self.assertEqual(abijo['position_from'], 'survey')
        self.assertGreater(abijo['buildings'], 0)
