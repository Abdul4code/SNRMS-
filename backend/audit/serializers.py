from rest_framework import serializers

from audit.models import ActivityLog


class ActorSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)


class ActivityLogSerializer(serializers.ModelSerializer):
    actor = ActorSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id',
            'actor',
            'action',
            'entity_type',
            'entity_id',
            'description',
            'metadata',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields
