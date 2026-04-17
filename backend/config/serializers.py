from rest_framework import serializers

from config.models import StreetType


class StreetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreetType
        fields = ['id', 'name', 'code', 'is_active', 'created_at']
        read_only_fields = fields


class StreetTypeCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=50)
    code = serializers.CharField(max_length=10)

    class Meta:
        model = StreetType
        fields = ['name', 'code']

    def validate_name(self, value):
        qs = StreetType.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'A street type with this name already exists.'
            )
        return value

    def validate_code(self, value):
        qs = StreetType.objects.filter(code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'A street type with this code already exists.'
            )
        return value
