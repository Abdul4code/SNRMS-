from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Application, ApplicationStatus, StatusHistory, Ward


class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = StatusHistory
        fields = [
            'id',
            'application',
            'from_status',
            'to_status',
            'changed_by',
            'remarks',
            'created_at',
        ]
        read_only_fields = fields

    def get_changed_by(self, obj):
        if obj.changed_by is None:
            return None
        return {
            'id': str(obj.changed_by.id),
            'full_name': obj.changed_by.full_name,
            'role': obj.changed_by.role,
        }


class DocumentSummarySerializer(serializers.Serializer):
    """Lightweight read-only document representation used inside ApplicationDetailSerializer."""
    id = serializers.UUIDField(read_only=True)
    document_type = serializers.CharField(read_only=True)
    original_filename = serializers.CharField(read_only=True)


class PaymentSummarySerializer(serializers.Serializer):
    """Lightweight read-only payment representation used inside ApplicationDetailSerializer."""
    id = serializers.UUIDField(read_only=True)
    stage = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    amount_expected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_submitted = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    payment_reference = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ApplicationListSerializer(serializers.ModelSerializer):
    street_type_name = serializers.CharField(source='street_type.name', read_only=True)
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'reference_number',
            'proposed_street_name',
            'street_type_name',
            'applicant_name',
            'status',
            'google_map_uploaded',
            'signpost_installed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class ApplicationDetailSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    street_type_name = serializers.CharField(source='street_type.name', read_only=True)
    ward_display = serializers.CharField(source='get_ward_display', read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    documents = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    certificate_file = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id',
            'reference_number',
            'applicant',
            'proposed_street_name',
            'street_type',
            'street_type_name',
            'location_description',
            'ward',
            'ward_display',
            'lga_area',
            'status',
            'committee_remarks',
            'chairman_remarks',
            'certificate_number',
            'certificate_file',
            'certificate_issued_at',
            'expires_at',
            'google_map_uploaded',
            'signpost_installed',
            'is_deleted',
            'created_at',
            'updated_at',
            'status_history',
            'documents',
            'payments',
        ]
        read_only_fields = fields

    def get_documents(self, obj):
        docs = obj.documents.filter(is_deleted=False)
        return DocumentSummarySerializer(docs, many=True).data

    def get_payments(self, obj):
        payments = obj.payments.all()
        return PaymentSummarySerializer(payments, many=True).data

    def get_certificate_file(self, obj):
        if not obj.certificate_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.certificate_file.url)
        return obj.certificate_file.url


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'id',
            'proposed_street_name',
            'street_type',
            'location_description',
            'ward',
            'lga_area',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['applicant'] = request.user
        return Application.objects.create(**validated_data)


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'proposed_street_name',
            'street_type',
            'location_description',
            'ward',
            'lga_area',
        ]

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status != ApplicationStatus.DRAFT:
            raise serializers.ValidationError(
                'Application can only be edited while in draft status.'
            )
        return attrs
