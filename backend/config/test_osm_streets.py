"""Matching OpenStreetMap centre-lines onto registry streets.

The registry holds where a street's buildings are, not where the street runs. The
importer borrows OSM's road geometry — but a name alone is not evidence, so these
check that a road is only accepted when it is also in the right place.
"""
import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from config.management.commands.import_osm_streets import name_key, normalise
from config.models import Street, StreetType


def way(name, points, way_id=1):
    """An OSM way as Overpass returns it: [(lat, lng), ...]."""
    return {'id': way_id, 'tags': {'name': name, 'highway': 'residential'},
            'geometry': [{'lat': la, 'lon': ln} for la, ln in points]}


def write_cache(tmp_path, ways):
    path = str(tmp_path)
    with open(path, 'w') as f:
        json.dump(ways, f)
    return path


class NameMatchingTests(TestCase):
    def test_a_type_word_does_not_stop_a_match(self):
        self.assertEqual(name_key('Akili Street'), name_key('Akili'))

    def test_spelling_noise_is_folded_away(self):
        self.assertEqual(normalise('Oke-Odo/Elemoro'), normalise('oke odo elemoro'))

    def test_different_streets_stay_different(self):
        self.assertNotEqual(name_key('Akili Street'), name_key('Bolarin Street'))


class ImportOsmStreetsTests(TestCase):
    def setUp(self):
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.cache = '/tmp/snrms_osm_test_cache.json'

    def street(self, name, lat=6.4700000, lng=3.6600000, **kw):
        return Street.objects.create(
            name=name, normalized_key=name.lower(), code=kw.pop('code', 'IBJ-ST-0001'),
            street_type=self.st, latitude=lat, longitude=lng, **kw)

    def run_import(self, ways, *args):
        write_cache(self.cache, ways)
        out = StringIO()
        call_command('import_osm_streets', '--cache', self.cache, *args, stdout=out)
        return out.getvalue()

    def test_a_street_gets_the_line_of_the_road_beside_it(self):
        s = self.street('Akili')
        self.run_import([way('Akili Street', [(6.47005, 3.66005), (6.47060, 3.66100)])])
        s.refresh_from_db()
        line = json.loads(s.geometry)
        self.assertEqual(line['type'], 'LineString')
        self.assertEqual(len(line['coordinates']), 2)
        self.assertAlmostEqual(line['coordinates'][0][0], 3.66005)   # lng first, GeoJSON

    def test_the_same_name_far_away_is_not_the_same_street(self):
        """The reason a name alone cannot be trusted: two towns, one name."""
        s = self.street('Church')
        self.run_import([way('Church Street', [(6.51000, 3.90000), (6.51050, 3.90100)])])
        s.refresh_from_db()
        self.assertEqual(s.geometry, '', 'a road 25 km away is a different street')

    def test_the_nearest_road_of_that_name_wins(self):
        s = self.street('Bolarin')
        self.run_import([
            way('Bolarin Street', [(6.47200, 3.66200), (6.47250, 3.66250)], way_id=1),
            way('Bolarin Street', [(6.47002, 3.66002), (6.47010, 3.66010)], way_id=2),
        ])
        s.refresh_from_db()
        self.assertAlmostEqual(json.loads(s.geometry)['coordinates'][0][1], 6.47002)

    def test_a_street_with_no_road_of_that_name_keeps_its_pin(self):
        s = self.street('Nowhere')
        self.run_import([way('Somewhere Else', [(6.47005, 3.66005), (6.47010, 3.66010)])])
        s.refresh_from_db()
        self.assertEqual(s.geometry, '')

    def test_an_exact_name_beats_a_stripped_one(self):
        """"Awoyaya Road" and "Awoyaya Street" must not share one road."""
        road = self.street('Awoyaya Road', code='IBJ-ST-0001')
        street = self.street('Awoyaya Street', code='IBJ-ST-0002')
        self.run_import([
            way('Awoyaya Road', [(6.47001, 3.66001), (6.47020, 3.66020)], way_id=1),
            way('Awoyaya Street', [(6.47003, 3.66003), (6.47040, 3.66040)], way_id=2),
        ])
        road.refresh_from_db(); street.refresh_from_db()
        self.assertNotEqual(road.geometry, street.geometry,
                            'each should take the road that carries its own name')

    def test_a_dry_run_changes_nothing(self):
        s = self.street('Akili')
        out = self.run_import(
            [way('Akili Street', [(6.47005, 3.66005), (6.47060, 3.66100)])], '--dry-run')
        s.refresh_from_db()
        self.assertEqual(s.geometry, '')
        self.assertIn('Would attach', out)

    def test_a_street_with_no_coordinates_is_left_alone_by_default(self):
        """The old-register streets: nothing to check a name against."""
        s = Street.objects.create(name='Akili', normalized_key='akili', code='IBJ-ST-0009',
                                  street_type=self.st)
        self.run_import([way('Akili Street', [(6.47005, 3.66005), (6.47060, 3.66100)])])
        s.refresh_from_db()
        self.assertEqual(s.geometry, '')

    def test_name_only_can_place_a_street_that_has_no_coordinates(self):
        s = Street.objects.create(name='Akili', normalized_key='akili', code='IBJ-ST-0010',
                                  street_type=self.st)
        self.run_import([way('Akili Street', [(6.47005, 3.66005), (6.47060, 3.66100)])],
                        '--name-only')
        s.refresh_from_db()
        self.assertTrue(s.geometry, 'a unique name in the LGA is enough to place it')
        self.assertIsNotNone(s.latitude, 'and it gains a location it did not have')

    def test_name_only_refuses_an_ambiguous_name(self):
        s = Street.objects.create(name='Church', normalized_key='church', code='IBJ-ST-0011',
                                  street_type=self.st)
        self.run_import([
            way('Church Street', [(6.47005, 3.66005), (6.47010, 3.66010)], way_id=1),
            way('Church Street', [(6.51000, 3.90000), (6.51010, 3.90010)], way_id=2),
        ], '--name-only')
        s.refresh_from_db()
        self.assertEqual(s.geometry, '', 'two roads share the name — which one is it?')
