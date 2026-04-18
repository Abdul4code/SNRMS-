import urllib.request
from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.views import APIView

from config.models import BuildingSurvey, StreetType
from config.serializers import BuildingSurveyMapSerializer, StreetTypeCreateSerializer, StreetTypeSerializer

ALLOWED_PHOTO_HOSTS = {'kf.kobotoolbox.org', 'kobofiles.org', 'kobocat.org'}


# ---------------------------------------------------------------------------
# Inline permission — avoids circular import with accounts app
# ---------------------------------------------------------------------------

class IsNamingCommittee(BasePermission):
    """Allow access only to users whose role is naming_committee."""

    message = 'Only naming committee members can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'naming_committee'
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
        return BuildingSurvey.objects.exclude(latitude=None).exclude(longitude=None)
