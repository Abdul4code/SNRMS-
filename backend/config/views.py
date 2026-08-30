from django.shortcuts import get_object_or_404
import urllib.request
from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from config.models import BuildingSurvey, RenewalSettings, Street, StreetType
from config.serializers import BuildingSurveyMapSerializer, RenewalSettingsSerializer, StreetSerializer, StreetTypeCreateSerializer, StreetTypeSerializer

ALLOWED_PHOTO_HOSTS = {'kf.kobotoolbox.org', 'kobofiles.org', 'kobocat.org'}


# ---------------------------------------------------------------------------
# Inline permission — avoids circular import with accounts app
# ---------------------------------------------------------------------------

# Valid coordinate box for Ibeju-Lekki LGA — filters out corrupt survey GPS points
# (e.g. lat/lng swapped, zeros, or wildly out-of-area readings).
IBEJU_LEKKI_BOUNDS = {'lat_min': 6.2, 'lat_max': 6.85, 'lng_min': 3.4, 'lng_max': 4.5}


class IsNamingCommittee(BasePermission):
    """Allow access only to users whose role is naming_committee."""

    message = 'Only naming committee members can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'naming_committee'
        )


class IsStreetManager(BasePermission):
    """Allow the Street Naming Committee or the Local Government Chairman."""

    message = 'Only the naming committee or chairman can manage streets.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('naming_committee', 'committee_chairman')
        )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class StreetTypeListView(ListCreateAPIView):
    """
    GET  /config/street-types/  — public list
    POST /config/street-types/  — committee chairman only
    """

    queryset = StreetType.objects.all()
    pagination_class = None  # small config list, always return all

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsNamingCommittee()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StreetTypeCreateSerializer
        return StreetTypeSerializer


class StreetTypeDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    /config/street-types/<pk>/  — authenticated
    PATCH  /config/street-types/<pk>/  — committee chairman only
    DELETE /config/street-types/<pk>/  — committee chairman only (soft delete)
    """

    queryset = StreetType.objects.all()
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsNamingCommittee()]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return StreetTypeCreateSerializer
        return StreetTypeSerializer

    def perform_destroy(self, instance):
        """Soft delete — set is_active=False instead of removing the record."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class RenewalSettingsView(APIView):
    """
    GET   /config/renewal-settings/  — any authenticated staff
    PATCH /config/renewal-settings/  — naming committee only
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instance = RenewalSettings.get()
        return Response(RenewalSettingsSerializer(instance).data)

    def patch(self, request):
        if request.user.role != 'naming_committee':
            return Response(
                {'detail': 'Only naming committee members can update renewal settings.'},
                status=403,
            )
        instance = RenewalSettings.get()
        serializer = RenewalSettingsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return Response(RenewalSettingsSerializer(instance).data)


class BuildingPhotoProxyView(APIView):
    """
    GET /config/building-surveys/photo/?url=<kobo_url>
    Proxies KoboToolbox attachment photos using the server-side API token.
    Public — <img> tags cannot send JWT headers, security is via domain whitelist.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        url = request.query_params.get('url', '').strip()
        if not url:
            raise Http404

        parsed = urlparse(url)
        if parsed.hostname not in ALLOWED_PHOTO_HOSTS:
            raise Http404

        headers = {'User-Agent': 'SNRMS/1.0'}
        token = getattr(settings, 'KOBO_API_TOKEN', '')
        if token:
            headers['Authorization'] = f'Token {token}'

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
                return HttpResponse(resp.read(), content_type=content_type)
        except Exception:
            raise Http404


class BuildingSurveyListView(ListAPIView):
    """
    GET /config/building-surveys/
    Returns ALL survey buildings that have coordinates (no pagination).
    Client-side highlighting is used for proposed-street filtering.
    """
    serializer_class = BuildingSurveyMapSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        b = IBEJU_LEKKI_BOUNDS
        return (
            BuildingSurvey.objects.exclude(latitude=None).exclude(longitude=None)
            .filter(latitude__range=(b['lat_min'], b['lat_max']),
                    longitude__range=(b['lng_min'], b['lng_max']))
        )


class StreetListView(ListAPIView):
    """GET /config/streets/ — canonical de-duplicated street registry."""
    serializer_class = StreetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Street.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(registration_status=status_filter)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        return qs


class StreetSummaryView(APIView):
    """GET /config/streets/summary/ — registry metrics for admin dashboards."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) == 'applicant':
            return Response({'detail': 'Not available.'}, status=status.HTTP_403_FORBIDDEN)
        b = IBEJU_LEKKI_BOUNDS
        named_streets = Street.objects.count()
        total_buildings = (
            BuildingSurvey.objects.exclude(latitude=None).exclude(longitude=None)
            .filter(latitude__range=(b['lat_min'], b['lat_max']),
                    longitude__range=(b['lng_min'], b['lng_max'])).count()
        )
        # Estimate unnamed streets by clustering unnamed points onto a ~90 m grid.
        unnamed_pts = (
            BuildingSurvey.objects.filter(street__isnull=True)
            .exclude(latitude=None).exclude(longitude=None)
            .filter(latitude__range=(b['lat_min'], b['lat_max']),
                    longitude__range=(b['lng_min'], b['lng_max']))
            .values_list('latitude', 'longitude')
        )
        cells = set()
        for lat, lng in unnamed_pts:
            cells.add((round(float(lat) / 0.0008), round(float(lng) / 0.0008)))
        unnamed_streets = len(cells)

        # Streets clicked for (re)naming = applications currently in the workflow.
        from applications.models import Application, ApplicationStatus
        inactive = {
            ApplicationStatus.DRAFT, ApplicationStatus.REJECTED_BY_COMMITTEE,
            ApplicationStatus.REJECTED_BY_CHAIRMAN, ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CERTIFICATE_ISSUED, ApplicationStatus.RENEWED,
        }
        renaming_in_progress = (
            Application.objects.filter(is_legacy=False)
            .exclude(status__in=inactive).exclude(is_deleted=True).count()
        )
        return Response({
            'total_buildings': total_buildings,
            'named_streets': named_streets,
            'unnamed_streets': unnamed_streets,
            'renaming_in_progress': renaming_in_progress,
        })


# ---------------------------------------------------------------------------
# Street registry management — merge, split, rename (staff only)
# ---------------------------------------------------------------------------
import re as _re  # noqa: E402
from django.db import transaction as _txn  # noqa: E402


def _next_street_code():
    from config.models import Street
    last = Street.objects.order_by('-code').values_list('code', flat=True).first()
    n = 0
    if last and last.startswith('IBJ-ST-'):
        try:
            n = int(last.rsplit('-', 1)[1])
        except ValueError:
            n = Street.objects.count()
    return f'IBJ-ST-{n + 1:04d}'


def _norm_key(name):
    s = (name or '').strip().lower()
    s = _re.sub(r'[^a-z0-9 ]', ' ', s)
    s = _re.sub(r'\s+', ' ', s).strip()
    return s


class StreetMergeView(APIView):
    """POST /config/streets/merge/ — merge source streets into a target street.

    Body: {"target_id": "...", "source_ids": ["...", "..."]}
    """
    permission_classes = [IsStreetManager]

    @_txn.atomic
    def post(self, request):
        target_id = request.data.get('target_id')
        source_ids = request.data.get('source_ids') or []
        if not target_id or not source_ids:
            return Response({'detail': 'target_id and source_ids are required.'}, status=status.HTTP_400_BAD_REQUEST)
        target = get_object_or_404(Street, pk=target_id)
        sources = list(Street.objects.filter(pk__in=source_ids).exclude(pk=target_id))
        if not sources:
            return Response({'detail': 'No valid source streets to merge.'}, status=status.HTTP_400_BAD_REQUEST)
        BuildingSurvey.objects.filter(street__in=sources).update(street=target)
        target.name_variants += sum(s.name_variants for s in sources)
        for s in sources:
            s.delete()
        target.building_count = target.buildings.count()
        target.save(update_fields=['name_variants', 'building_count'])
        return Response({'merged': len(sources), 'target': StreetSerializer(target).data})


class StreetSplitView(APIView):
    """POST /config/streets/<pk>/split/ — move some buildings to a new street.

    Body: {"name": "New Street Name", "building_ids": [kobo_id, ...], "street_type_id": "..."(optional)}
    """
    permission_classes = [IsStreetManager]

    @_txn.atomic
    def post(self, request, pk):
        street = get_object_or_404(Street, pk=pk)
        name = (request.data.get('name') or '').strip()
        building_ids = request.data.get('building_ids') or []
        if not name or not building_ids:
            return Response({'detail': 'name and building_ids are required.'}, status=status.HTTP_400_BAD_REQUEST)

        key = _norm_key(name)
        # Ensure a unique normalized_key.
        base_key, i = key, 2
        while Street.objects.filter(normalized_key=key).exists():
            key = f'{base_key} {i}'
            i += 1

        st = None
        st_id = request.data.get('street_type_id')
        if st_id:
            st = StreetType.objects.filter(pk=st_id).first()

        new_street = Street.objects.create(
            name=name.title(), normalized_key=key, code=_next_street_code(),
            street_type=st or street.street_type, ward=street.ward, locality=street.locality,
        )
        moved = BuildingSurvey.objects.filter(kobo_id__in=building_ids, street=street).update(street=new_street)
        new_street.building_count = new_street.buildings.count()
        new_street.save(update_fields=['building_count'])
        street.building_count = street.buildings.count()
        street.save(update_fields=['building_count'])
        return Response({'moved': moved, 'new_street': StreetSerializer(new_street).data}, status=status.HTTP_201_CREATED)


class StreetUpdateView(APIView):
    """PATCH /config/streets/<pk>/ — rename a street or set its type / status."""
    permission_classes = [IsStreetManager]

    def patch(self, request, pk):
        street = get_object_or_404(Street, pk=pk)
        name = request.data.get('name')
        if name:
            street.name = name.strip().title()
        st_id = request.data.get('street_type_id')
        if st_id:
            street.street_type = StreetType.objects.filter(pk=st_id).first()
        reg = request.data.get('registration_status')
        if reg in dict(Street.RegistrationStatus.choices):
            street.registration_status = reg
        street.save()
        return Response(StreetSerializer(street).data)


class StreetBuildingsView(ListAPIView):
    """GET /config/streets/<pk>/buildings/ — buildings currently on a street (for split UI)."""
    serializer_class = BuildingSurveyMapSerializer
    permission_classes = [IsStreetManager]
    pagination_class = None

    def get_queryset(self):
        return BuildingSurvey.objects.filter(street_id=self.kwargs['pk'])


class LocalityWardView(APIView):
    """GET /config/locality-wards/ — authoritative community -> ward mapping.

    Loaded from the LGA's official community/ward list (config/data/illg_wards.json):
    7 wards (Ibeju 1-2, Orimedu 1-3, Iwerekun 1-2) across 110 communities.
    """
    permission_classes = [AllowAny]
    _cache = None

    def get(self, request):
        import json
        import os
        from django.conf import settings as dj_settings
        if LocalityWardView._cache is None:
            path = os.path.join(dj_settings.BASE_DIR, 'config', 'data', 'illg_wards.json')
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            LocalityWardView._cache = data
        data = LocalityWardView._cache
        return Response({
            'wards': data['ward_names'],
            'community_to_ward': data['community_to_ward'],
        })


class RoadNetworkView(APIView):
    """GET /config/road-network/?bbox=south,west,north,east — roads in view.

    The layer the applicant taps to say "this is my street". Geometry only: OSM
    names barely a twentieth of the roads here, and the name is not what we want
    from it anyway. Without a bbox the whole LGA comes back — about 4,500
    segments, which is a couple of megabytes and fine to hold in a browser.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from config.models import RoadSegment
        qs = RoadSegment.objects.all()
        raw = request.query_params.get('bbox') or ''
        if raw:
            try:
                south, west, north, east = [float(x) for x in raw.split(',')]
            except ValueError:
                return Response({'detail': 'bbox must be south,west,north,east'},
                                status=400)
            # Overlap, not containment: a road crossing the view still belongs in it.
            qs = qs.filter(min_lat__lte=north, max_lat__gte=south,
                           min_lng__lte=east, max_lng__gte=west)
        return Response([
            {'id': r.osm_id, 'name': r.name, 'geometry': r.geometry}
            for r in qs.only('osm_id', 'name', 'geometry')
        ])


class CommunityListView(APIView):
    """GET /config/communities/ — flat list of official community names (for pickers)."""
    permission_classes = [AllowAny]

    def get(self, request):
        from applications.localities import official_communities
        return Response(official_communities())


def _bearing(lat1, lng1, lat2, lng2):
    """Compass bearing (degrees) from point 1 toward point 2."""
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


class StreetViewProxyView(APIView):
    """GET /config/streetview/?lat=&lng= — a Google Street View image of a location.

    Keeps the Google Maps API key server-side. Returns the actual street-level
    photo so an <img> tag can display it. Because Street View coverage in
    Ibeju-Lekki is sparse, we search for the nearest *outdoor* panorama within
    ~1 km and aim the camera back toward the selected spot — so it shows the
    street rather than 404-ing (which would leave only the satellite fallback).
    404 only when no key is configured or no street imagery exists nearby.
    """
    permission_classes = [AllowAny]
    SEARCH_RADIUS_M = 1000

    def get(self, request):
        key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
        if not key:
            raise Http404
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            raise Http404
        size = request.query_params.get('size', '640x360')
        radius = self.SEARCH_RADIUS_M

        # Find the nearest outdoor street panorama; 404 cleanly if there's none.
        pano_lat = pano_lng = None
        meta = (f'https://maps.googleapis.com/maps/api/streetview/metadata'
                f'?location={lat},{lng}&radius={radius}&source=outdoor&key={key}')
        try:
            import json as _json
            with urllib.request.urlopen(meta, timeout=10) as m:
                data = _json.loads(m.read())
            if data.get('status') != 'OK':
                raise Http404
            loc = data.get('location') or {}
            pano_lat, pano_lng = loc.get('lat'), loc.get('lng')
        except Http404:
            raise
        except Exception:
            pass  # metadata call failed — still attempt the image below

        # Aim the camera from the panorama toward the selected point.
        heading = request.query_params.get('heading', '')
        if not heading and pano_lat is not None and pano_lng is not None:
            heading = f'{_bearing(pano_lat, pano_lng, lat, lng):.0f}'

        img = (f'https://maps.googleapis.com/maps/api/streetview'
               f'?size={size}&location={lat},{lng}&radius={radius}&source=outdoor&fov=80&key={key}')
        if heading != '':
            img += f'&heading={heading}'
        try:
            with urllib.request.urlopen(img, timeout=15) as resp:
                return HttpResponse(resp.read(),
                                    content_type=resp.headers.get('Content-Type', 'image/jpeg'))
        except Exception:
            raise Http404


class PublicSettingsView(APIView):
    """GET /config/public-settings/ — non-secret flags the frontend needs."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'google_maps_enabled': bool(getattr(settings, 'GOOGLE_MAPS_API_KEY', '')),
        })
