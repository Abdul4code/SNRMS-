"""The register can only be trusted onto the map if wrong answers are thrown away.

A geocoder would rather return something than nothing, so these tests are about
what gets rejected, not what gets found.
"""
from django.test import SimpleTestCase

from config.management.commands.geocode_registered_streets import (
    metres, names_agree, strip_titles,
)


class StripTitlesTests(SimpleTestCase):
    def test_removes_stacked_honorifics(self):
        self.assertEqual(strip_titles('Alh. Prince Ganiyu Eletu Street'),
                         'Ganiyu Eletu Street')
        self.assertEqual(strip_titles('Brig. Gen. Life Ajemba Street'),
                         'Life Ajemba Street')

    def test_leaves_a_plain_name_alone(self):
        self.assertEqual(strip_titles('Marble Street'), 'Marble Street')

    def test_does_not_eat_a_name_that_starts_like_a_title(self):
        # "Drive" is not "Dr.", "Princess Road" is a road named Princess.
        self.assertEqual(strip_titles('Drivers Close'), 'Drivers Close')


class NamesAgreeTests(SimpleTestCase):
    def test_accepts_the_same_street_spelled_differently(self):
        self.assertTrue(names_agree('Atanda Badmus Street', 'Atanda Badmus Street'))
        self.assertTrue(names_agree('Alh. Tolani Bakare Street', 'Tolani Bakare Street'))
        self.assertTrue(names_agree('Akanbi Sabiu Odofin Street', 'Akanbi Odofin Street'))

    def test_accepts_a_different_street_type(self):
        # The register and Google disagree on Close vs Street often enough; the
        # people are the same, so it is the same street.
        self.assertTrue(names_agree('Dorothy Agunpopo Street', 'Dorothy Agunpopo Close'))

    def test_rejects_a_single_shared_word(self):
        # This is the one that used to get through: one common word is coincidence.
        self.assertFalse(names_agree('S.D.A Church Road', 'Church Street'))

    def test_rejects_a_shared_surname(self):
        # Balogun and Adebayo recur across unrelated streets in the register.
        self.assertFalse(names_agree('Prince Bayo Balogun Way', 'Tunde Balogun Street'))
        self.assertFalse(names_agree('Alhaji Sheik Rabiu Adebayo Street',
                                     'Adebayo Folarin Street'))

    def test_rejects_a_bare_type_word(self):
        self.assertFalse(names_agree('Ocean Drive', 'Drive'))

    def test_a_one_word_name_must_match_exactly(self):
        self.assertTrue(names_agree('Marble Street', 'Marble Street'))
        self.assertFalse(names_agree('Marble Street', 'Marble Arch Street'))

    def test_rejects_empty(self):
        self.assertFalse(names_agree('', 'Marble Street'))
        self.assertFalse(names_agree('Marble Street', ''))
        self.assertFalse(names_agree('Street', 'Street'))


class MetresTests(SimpleTestCase):
    def test_measures_a_known_separation(self):
        # ~1 minute of latitude is about 1.85 km.
        self.assertAlmostEqual(metres(6.47, 3.81, 6.4867, 3.81), 1853, delta=40)

    def test_is_zero_for_the_same_point(self):
        self.assertEqual(round(metres(6.47, 3.81, 6.47, 3.81)), 0)
