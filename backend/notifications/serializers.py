from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(source='application.id', read_only=True, allow_null=True)
    application_reference = serializers.CharField(
        source='application.reference_number', read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'application_id',
            'application_reference',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields
