from urllib.parse import quote

from rest_framework import serializers

from config.models import BuildingSurvey, RenewalSettings, StreetType


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


class RenewalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RenewalSettings
        fields = ['renewal_years', 'updated_at']
        read_only_fields = ['updated_at']

    def validate_renewal_years(self, value):
        if value < 1 or value > 99:
            raise serializers.ValidationError('Renewal years must be between 1 and 99.')
        return value


class BuildingSurveyMapSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = BuildingSurvey
        fields = [
            'kobo_id',
            'latitude',
            'longitude',
            'proposed_street_name',
            'proposed_auto_number',
            'building_use',
            'building_type',
            'building_type_other',
            'locality',
            'ward',
            'number_of_floors',
            'number_of_flats',
            'number_of_shops',
            'occupancy_type',
            'photo_url',
        ]

    def get_photo_url(self, obj):
        if not obj.photo_url:
            return ''
        request = self.context.get('request')
        proxy = f'/api/config/building-surveys/photo/?url={quote(obj.photo_url, safe="")}'
        return request.build_absolute_uri(proxy) if request else proxy
