from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated

from config.models import StreetType
from config.serializers import StreetTypeCreateSerializer, StreetTypeSerializer


# ---------------------------------------------------------------------------
# Inline permission — avoids circular import with accounts app
# ---------------------------------------------------------------------------

class IsCommitteeChairman(BasePermission):
    """Allow access only to users whose role is committee_chairman."""

    message = 'Only the committee chairman can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'committee_chairman'
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
        return [IsCommitteeChairman()]

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
        return [IsCommitteeChairman()]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return StreetTypeCreateSerializer
        return StreetTypeSerializer

    def perform_destroy(self, instance):
        """Soft delete — set is_active=False instead of removing the record."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])
