from rest_framework.generics import ListAPIView
from rest_framework.permissions import BasePermission

from audit.models import ActivityLog
from audit.serializers import ActivityLogSerializer


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

class ActivityLogListView(ListAPIView):
    """
    GET /audit/logs/
    Returns paginated activity logs. Committee chairman only.
    Optional query params:
      ?entity_type=<str>  — filter by entity_type
      ?actor=<uuid>       — filter by actor id
    """

    serializer_class = ActivityLogSerializer
    permission_classes = [IsCommitteeChairman]

    def get_queryset(self):
        qs = ActivityLog.objects.select_related('actor').all()

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        actor = self.request.query_params.get('actor')
        if actor:
            qs = qs.filter(actor__id=actor)

        return qs
