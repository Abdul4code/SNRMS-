"""The road layer an applicant taps to say "this is my street"."""
import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from applications.models import Application, ApplicationStatus
from config.models import RoadSegment, StreetType


def osm_way(way_id, points, name='', highway='residential'):
    return {'id': way_id, 'tags': {'name': name, 'highway': highway},
            'geometry': [{'lat': la, 'lon': ln} for la, ln in points]}


class ImportRoadNetworkTests(TestCase):
    CACHE = '/tmp/snrms_roads_test.json'

    def run_import(self, ways, *args):
        with open(self.CACHE, 'w') as f:
            json.dump(ways, f)
        out = StringIO()
        call_command('import_road_network', '--cache', self.CACHE, *args, stdout=out)
        return out.getvalue()

    def test_unnamed_roads_are_imported_too(self):
        """The whole point: OSM names a twentieth of the roads but maps nearly all."""
        self.run_import([
            osm_way(1, [(6.4700, 3.6600), (6.4710, 3.6610)], name='Akili Street'),
            osm_way(2, [(6.4720, 3.6620), (6.4730, 3.6630)], name=''),
            osm_way(3, [(6.4740, 3.6640), (6.4750, 3.6650)], name=''),
        ])
        self.assertEqual(RoadSegment.objects.count(), 3)
        self.assertEqual(RoadSegment.objects.exclude(name='').count(), 1)

    def test_footpaths_and_slip_roads_are_left_out(self):
        self.run_import([
            osm_way(1, [(6.470, 3.660), (6.471, 3.661)], highway='residential'),
            osm_way(2, [(6.472, 3.662), (6.473, 3.663)], highway='footway'),
            osm_way(3, [(6.474, 3.664), (6.475, 3.665)], highway='motorway_link'),
        ])
        self.assertEqual(RoadSegment.objects.count(), 1)

    def test_the_bounding_box_is_stored_for_lookups(self):
        self.run_import([osm_way(1, [(6.4700, 3.6600), (6.4750, 3.6650)])])
        seg = RoadSegment.objects.get(osm_id=1)
        self.assertAlmostEqual(float(seg.min_lat), 6.4700)
        self.assertAlmostEqual(float(seg.max_lat), 6.4750)

    def test_rerunning_refreshes_rather_than_duplicates(self):
        self.run_import([osm_way(1, [(6.470, 3.660), (6.471, 3.661)], name='Old')])
        self.run_import([osm_way(1, [(6.470, 3.660), (6.471, 3.661)], name='New')])
        self.assertEqual(RoadSegment.objects.count(), 1)
        self.assertEqual(RoadSegment.objects.get(osm_id=1).name, 'New')

    def test_a_dry_run_writes_nothing(self):
        out = self.run_import([osm_way(1, [(6.470, 3.660), (6.471, 3.661)])], '--dry-run')
        self.assertEqual(RoadSegment.objects.count(), 0)
        self.assertIn('Would import', out)

    def test_a_one_point_way_is_not_a_road(self):
        self.run_import([osm_way(1, [(6.470, 3.660)])])
        self.assertEqual(RoadSegment.objects.count(), 0)


class RoadNetworkEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='road@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        RoadSegment.objects.create(
            osm_id=1, name='Near Road', highway='residential',
            geometry=json.dumps({'type': 'LineString',
                                 'coordinates': [[3.6600, 6.4700], [3.6610, 6.4710]]}),
            min_lat=6.4700, max_lat=6.4710, min_lng=3.6600, max_lng=3.6610)
        RoadSegment.objects.create(
            osm_id=2, name='Far Road', highway='residential',
            geometry=json.dumps({'type': 'LineString',
                                 'coordinates': [[3.9000, 6.5100], [3.9010, 6.5110]]}),
            min_lat=6.5100, max_lat=6.5110, min_lng=3.9000, max_lng=3.9010)

    def test_a_bbox_returns_only_the_roads_in_view(self):
        r = self.client.get('/api/config/road-network/?bbox=6.469,3.659,6.472,3.662')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x['id'] for x in r.data], [1])

    def test_a_road_crossing_the_view_still_counts(self):
        """Overlap, not containment — a long road must not vanish when zoomed in."""
        r = self.client.get('/api/config/road-network/?bbox=6.4703,3.6603,6.4705,3.6605')
        self.assertEqual([x['id'] for x in r.data], [1])

    def test_without_a_bbox_the_whole_network_comes_back(self):
        r = self.client.get('/api/config/road-network/')
        self.assertEqual(len(r.data), 2)

    def test_a_bad_bbox_is_refused_clearly(self):
        r = self.client.get('/api/config/road-network/?bbox=nonsense')
        self.assertEqual(r.status_code, 400)

    def test_it_needs_a_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/config/road-network/').status_code, 401)


class CapturedStreetLineTests(TestCase):
    """The line the applicant tapped is kept on their application."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='line@example.com', password='x', first_name='A', last_name='B',
            role=Role.APPLICANT)
        self.st = StreetType.objects.create(name='Street', code='ST')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.line = json.dumps({'type': 'LineString',
                                'coordinates': [[3.6600, 6.4700], [3.6610, 6.4710]]})

    def test_the_tapped_line_is_saved_with_the_application(self):
        r = self.client.post('/api/applications/', {
            'proposed_street_name': 'Akili', 'location_description': '6.47,3.66',
            'locality': 'Abijo', 'latitude': '6.4705000', 'longitude': '3.6605000',
            'street_type': str(self.st.id), 'street_line': self.line,
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content[:300])
        self.assertEqual(Application.objects.get(pk=r.data['id']).street_line, self.line)

    def test_the_map_is_given_the_applicants_own_line(self):
        app = Application.objects.create(
            applicant=self.user, proposed_street_name='Akili', location_description='d',
            street_type=self.st, latitude='6.4705000', longitude='3.6605000',
            street_line=self.line, status=ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)
        r = self.client.get(f'/api/applications/{app.id}/')
        self.assertEqual(r.data['street_geometry'], self.line)

    def test_an_application_with_only_a_pin_has_no_line(self):
        app = Application.objects.create(
            applicant=self.user, proposed_street_name='Nowhere', location_description='d',
            street_type=self.st, latitude='6.4705000', longitude='3.6605000',
            status=ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW)
        r = self.client.get(f'/api/applications/{app.id}/')
        self.assertIsNone(r.data['street_geometry'])
