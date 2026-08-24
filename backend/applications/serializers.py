from rest_framework import serializers

from accounts.models import Role
from accounts.serializers import UserSerializer
from .models import Application, ApplicationStatus, StatusHistory, Ward
from .street_locks import applications_at_location, hold_message, lock_state
from config.models import StreetType



# Street-type words (and common abbreviations) that applicants often type at the
# end of the name. The selected Street Type already covers this, so it is
# stripped internally to keep the registry clean and duplicate checks accurate.
_TYPE_SUFFIXES = {
    'street', 'st', 'str', 'streeet', 'road', 'rd', 'close', 'cl', 'avenue', 'ave', 'av',
    'crescent', 'cres', 'cresent', 'cr', 'drive', 'dr', 'lane', 'ln', 'way',
    'boulevard', 'blvd', 'court', 'ct', 'place', 'pl', 'terrace', 'ter',
    'gardens', 'garden', 'gdns', 'rise', 'grove', 'grv', 'mews', 'parkway',
    'pkwy', 'esplanade', 'circus', 'plaza', 'mall',
}


def strip_street_type_suffix(name: str) -> str:
    """Remove a trailing street-type word: "Ajose Street" -> "Ajose"."""
    import re as _re
    cleaned = _re.sub(r'\s+', ' ', (name or '').strip())
    while True:
        parts = cleaned.split()
        if len(parts) >= 2 and parts[-1].lower().strip('.,') in _TYPE_SUFFIXES:
            cleaned = ' '.join(parts[:-1]).strip()
            continue
        break
    return cleaned or (name or '').strip()


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
            'is_legacy',      # lets every queue show new-application vs validation
            'google_map_uploaded',
            'signpost_installed',
            'expires_at',
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
    legacy_certificate_url = serializers.SerializerMethodField()
    street_hold = serializers.SerializerMethodField()
    location_contention = serializers.SerializerMethodField()

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
            'locality',
            'latitude',
            'longitude',
            'lga_area',
            'status',
            'is_legacy',
            'committee_remarks',
            'chairman_remarks',
            'certificate_number',
            'certificate_file',
            'certificate_released',
            'signboard_number',
            'pole_number',
            'is_royalty_exempt',
            'legacy_certificate_url',
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
            'street_hold',
            'location_contention',
        ]
        read_only_fields = fields

    def get_street_hold(self, obj):
        """Whether this application still holds its street, and for how long —
        so the applicant can be told to pay before the hold lapses."""
        if obj.is_legacy:
            return None
        state = lock_state(obj)
        if state['kind'] == 'none':
            return None
        return {**state, 'message': hold_message(obj, state)}

    def get_location_contention(self, obj):
        """Other applications for the same street, oldest first. Staff only — it
        names other applicants, which one applicant may not see about another."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or getattr(user, 'role', None) == Role.APPLICANT:
            return None
        return applications_at_location(obj)

    def get_documents(self, obj):
        docs = obj.documents.filter(is_deleted=False)
        return DocumentSummarySerializer(docs, many=True).data

    def get_payments(self, obj):
        payments = obj.payments.all()
        return PaymentSummarySerializer(payments, many=True).data

    def get_certificate_file(self, obj):
        # Signed link, not a raw /media/ path: public media serving is off in
        # production, so a raw path 404s wherever it is opened.
        from snrms.media_access import signed_media_url
        return signed_media_url(obj.certificate_file, self.context.get('request'))

    def get_legacy_certificate_url(self, obj):
        """The document a validate applicant uploaded — the committee reviews it."""
        from snrms.media_access import signed_media_url
        return signed_media_url(obj.legacy_certificate, self.context.get('request'))


class ApplicationCreateSerializer(serializers.ModelSerializer):
    legacy_certificate = serializers.FileField(required=False, allow_null=True)
    street_type = serializers.PrimaryKeyRelatedField(
        queryset=StreetType.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'proposed_street_name',
            'street_type',
            'location_description',
            'ward',
            'locality',
            'latitude',
            'longitude',
            'lga_area',
            'is_legacy',
            'legacy_certificate',
        ]
        read_only_fields = ['id']

    def validate_proposed_street_name(self, value):
        return strip_street_type_suffix(value)

    def validate(self, attrs):
        if attrs.get('is_legacy') and not attrs.get('legacy_certificate'):
            raise serializers.ValidationError(
                {'legacy_certificate': 'Please upload your existing certificate for legacy registration.'}
            )
        if not attrs.get('is_legacy') and not attrs.get('street_type'):
            raise serializers.ValidationError({'street_type': 'Street type is required.'})
        return attrs

    def create(self, validated_data):
        from config.models import StreetType
        from .wards import resolve_ward
        request = self.context.get('request')
        validated_data['applicant'] = request.user
        # Validate-existing-registration flow may not carry a street type — default it.
        if not validated_data.get('street_type'):
            validated_data['street_type'] = (
                StreetType.objects.filter(name__iexact='Street').first()
                or StreetType.objects.first()
            )
        # The applicant is no longer asked for a ward — a locality sits in one ward,
        # so it is derived here rather than taken on trust from the form.
        validated_data['ward'] = resolve_ward(
            validated_data.get('locality'),
            validated_data.get('latitude'),
            validated_data.get('longitude'),
            fallback=validated_data.get('ward', ''),
        )
        return Application.objects.create(**validated_data)


class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'proposed_street_name',
            'street_type',
            'location_description',
            'ward',
            'locality',
            'latitude',
            'longitude',
            'lga_area',
        ]

    def validate_proposed_street_name(self, value):
        return strip_street_type_suffix(value)

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status != ApplicationStatus.DRAFT:
            raise serializers.ValidationError(
                'Application can only be edited while in draft status.'
            )
        return attrs
