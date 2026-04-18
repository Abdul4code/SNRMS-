from rest_framework import serializers

from config.models import FeeComponent, FeeConfiguration, StreetType

from .models import Payment, PaymentStatus


# ---------------------------------------------------------------------------
# Nested helpers
# ---------------------------------------------------------------------------

class _ConfirmedBySerializer(serializers.Serializer):
    """Minimal representation of the finance user who confirmed a payment."""
    id = serializers.UUIDField()
    full_name = serializers.CharField()


# ---------------------------------------------------------------------------
# PaymentSerializer — full read-only
# ---------------------------------------------------------------------------

class PaymentSerializer(serializers.ModelSerializer):
    confirmed_by = _ConfirmedBySerializer(read_only=True)
    submitted_by_id = serializers.UUIDField(source='submitted_by.id', read_only=True, allow_null=True)
    submitted_by_name = serializers.CharField(source='submitted_by.full_name', read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'application',
            'stage',
            'status',
            'amount_expected',
            'amount_submitted',
            'payment_reference',
            'bank_name',
            'payment_date',
            'receipt_file',
            'confirmed_by',
            'confirmed_at',
            'finance_remarks',
            'submitted_by_id',
            'submitted_by_name',
            'submitted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# PaymentSubmitSerializer — applicant submits payment reference
# ---------------------------------------------------------------------------

class PaymentSubmitSerializer(serializers.Serializer):
    payment_reference = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    payment_date = serializers.DateField(required=False, allow_null=True)
    amount_submitted = serializers.DecimalField(max_digits=12, decimal_places=2)
    receipt_file = serializers.FileField(required=False, allow_null=True)

    def validate_amount_submitted(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount submitted must be greater than zero.')
        return value

    def validate(self, attrs):
        amount = attrs.get('amount_submitted')
        if amount is not None and amount <= 0:
            raise serializers.ValidationError(
                {'amount_submitted': 'Amount submitted must be greater than zero.'}
            )
        return attrs


# ---------------------------------------------------------------------------
# PaymentConfirmSerializer — finance confirms or rejects a payment
# ---------------------------------------------------------------------------

class PaymentConfirmSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[PaymentStatus.CONFIRMED, PaymentStatus.REJECTED]
    )
    finance_remarks = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        if value not in (PaymentStatus.CONFIRMED, PaymentStatus.REJECTED):
            raise serializers.ValidationError(
                'Status must be either "confirmed" or "rejected".'
            )
        return value


# ---------------------------------------------------------------------------
# FeeConfigurationSerializer — read-only list view
# ---------------------------------------------------------------------------

_COMPONENT_STAGE = {
    'application_fee': 'stage_a',
    'inspection_fee': 'stage_a',
    'radio_tv_tax': 'stage_a',
    'committee_verification_fee': 'stage_a',
    'street_name_fee': 'stage_c',
    'signpost_installation_fee': 'stage_c',
    'map_upload_fee': 'stage_c',
    'renewal_fee': 'renewal',
}


class FeeConfigurationSerializer(serializers.ModelSerializer):
    fee_type = serializers.CharField(source='component', read_only=True)
    fee_type_display = serializers.CharField(source='get_component_display', read_only=True)
    stage = serializers.SerializerMethodField()
    street_type_id = serializers.UUIDField(source='street_type.id', read_only=True, allow_null=True)
    street_type_name = serializers.CharField(source='street_type.name', read_only=True, allow_null=True)

    class Meta:
        model = FeeConfiguration
        fields = [
            'id',
            'component',
            'fee_type',
            'fee_type_display',
            'stage',
            'amount',
            'street_type_id',
            'street_type_name',
            'is_active',
            'updated_at',
        ]
        read_only_fields = fields

    def get_stage(self, obj):
        return _COMPONENT_STAGE.get(obj.component)


# ---------------------------------------------------------------------------
# FeeConfigurationCreateSerializer — create a new fee configuration
# ---------------------------------------------------------------------------

class FeeConfigurationCreateSerializer(serializers.ModelSerializer):
    street_type = serializers.PrimaryKeyRelatedField(
        queryset=StreetType.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = FeeConfiguration
        fields = ['component', 'amount', 'street_type', 'is_active']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, attrs):
        component = attrs.get('component', '')
        street_type = attrs.get('street_type')
        if component == FeeComponent.STREET_NAME_FEE and not street_type:
            raise serializers.ValidationError(
                {'street_type': 'Street type is required for Street Name Fee.'}
            )
        if component != FeeComponent.STREET_NAME_FEE:
            attrs['street_type'] = None
        return attrs


# ---------------------------------------------------------------------------
# FeeConfigurationUpdateSerializer — update component, amount, street_type, is_active
# ---------------------------------------------------------------------------

class FeeConfigurationUpdateSerializer(serializers.ModelSerializer):
    component = serializers.ChoiceField(choices=FeeComponent.choices, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    street_type = serializers.PrimaryKeyRelatedField(
        queryset=StreetType.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = FeeConfiguration
        fields = ['component', 'amount', 'street_type', 'is_active']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, attrs):
        component = attrs.get('component', self.instance.component if self.instance else '')
        if 'street_type' in attrs:
            street_type = attrs['street_type']
        else:
            street_type = getattr(self.instance, 'street_type', None)
        if component == FeeComponent.STREET_NAME_FEE and not street_type:
            raise serializers.ValidationError(
                {'street_type': 'Street type is required for Street Name Fee.'}
            )
        if component != FeeComponent.STREET_NAME_FEE:
            attrs['street_type'] = None
        return attrs
