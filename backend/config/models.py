import uuid
from django.db import models


class BuildingUse(models.TextChoices):
    RESIDENTIAL = 'residential', 'Residential'
    COMMERCIAL = 'commercial', 'Commercial'
    MIXED = 'mixed', 'Mixed'
    INSTITUTIONAL = 'institutional', 'Institutional'
    OTHER = 'other', 'Other'


class BuildingType(models.TextChoices):
    DETACHED = 'detached', 'Detached'
    SEMI_DETACHED = 'semi_detached', 'Semi-Detached'
    FLAT = 'flat', 'Flat'
    BUNGALOW = 'bungalow', 'Bungalow'
    STOREY_BUILDING = 'storey_building', 'Storey Building'
    OTHERS = 'others', 'Others'


class OccupancyType(models.TextChoices):
    OWNER_OCCUPIED = 'owner_occupied', 'Owner Occupied'
    TENANT = 'tenant', 'Tenant'
    VACANT = 'vacant', 'Vacant'
    UNDER_CONSTRUCTION = 'under_construction', 'Under Construction'


class AccessType(models.TextChoices):
    TARRED_ROAD = 'tarred_road', 'Tarred Road'
    UNTARRED_ROAD = 'untarred_road', 'Untarred Road'
    FOOTPATH = 'footpath', 'Footpath'
    WATERWAY = 'waterway', 'Waterway'


class WaterSupply(models.TextChoices):
    BOREHOLE = 'borehole', 'Borehole'
    PUBLIC_TAP = 'public_tap', 'Public Tap'
    NONE = 'none', 'None'


class WasteCollection(models.TextChoices):
    REGULAR = 'regular', 'Regular'
    IRREGULAR = 'irregular', 'Irregular'
    NONE = 'none', 'None'


class StreetType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'street_types'
        ordering = ['name']

    def __str__(self):
        return self.name


class FeeComponent(models.TextChoices):
    # Stage A components
    APPLICATION_FEE = 'application_fee', 'Application Fee'
    INSPECTION_FEE = 'inspection_fee', 'Inspection Fee'
    RADIO_TV_TAX = 'radio_tv_tax', 'Radio/TV Tax'
    COMMITTEE_VERIFICATION_FEE = 'committee_verification_fee', 'Committee Verification Fee'
    # Stage C components
    STREET_NAME_FEE = 'street_name_fee', 'Street Name Fee'
    SIGNPOST_INSTALLATION_FEE = 'signpost_installation_fee', 'Signpost Installation Fee'
    MAP_UPLOAD_FEE = 'map_upload_fee', 'Map Upload Fee'
    # Renewal
    RENEWAL_FEE = 'renewal_fee', 'Renewal Fee'


class FeeConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    component = models.CharField(max_length=50, choices=FeeComponent.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    street_type = models.ForeignKey(
        StreetType, null=True, blank=True, on_delete=models.SET_NULL,
        help_text='Only for street_name_fee — varies per street type'
    )
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        'accounts.User', null=True, on_delete=models.SET_NULL,
        related_name='fee_configs_updated'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fee_configurations'
        unique_together = [['component', 'street_type']]

    def __str__(self):
        return f'{self.component}: {self.amount}'


class RenewalSettings(models.Model):
    """Singleton — always use RenewalSettings.get() to read/write."""
    renewal_years = models.PositiveSmallIntegerField(
        default=5,
        help_text='Number of years added to the current expiry date when a renewal is confirmed.',
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='renewal_settings_updates',
    )

    class Meta:
        db_table = 'renewal_settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f'Renewal: {self.renewal_years} year(s)'


class BuildingSurvey(models.Model):
    kobo_id = models.IntegerField(unique=True)
    kobo_uuid = models.UUIDField(unique=True)
    submission_time = models.DateTimeField(null=True, blank=True)
    enumerator_id = models.CharField(max_length=100, blank=True)
    survey_date = models.DateField(null=True, blank=True)

    locality = models.CharField(max_length=200, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    existing_street_name = models.CharField(max_length=200, blank=True)
    proposed_street_name = models.CharField(max_length=200, blank=True)
    existing_house_number = models.CharField(max_length=50, blank=True)
    proposed_auto_number = models.CharField(max_length=50, blank=True)

    building_use = models.CharField(max_length=20, choices=BuildingUse.choices, blank=True)
    building_type = models.CharField(max_length=20, choices=BuildingType.choices, blank=True)
    building_type_other = models.CharField(max_length=200, blank=True)
    number_of_floors = models.PositiveSmallIntegerField(null=True, blank=True)
    number_of_flats = models.PositiveSmallIntegerField(null=True, blank=True)
    number_of_shops = models.PositiveSmallIntegerField(null=True, blank=True)

    compound_fence = models.BooleanField(null=True, blank=True)
    occupancy_type = models.CharField(max_length=20, choices=OccupancyType.choices, blank=True)
    primary_access_type = models.CharField(max_length=20, choices=AccessType.choices, blank=True)
    vehicle_accessible = models.BooleanField(null=True, blank=True)
    electricity_connection = models.BooleanField(null=True, blank=True)
    water_supply = models.CharField(max_length=20, choices=WaterSupply.choices, blank=True)
    waste_collection = models.CharField(max_length=20, choices=WasteCollection.choices, blank=True)

    nearby_landmark = models.CharField(max_length=500, blank=True)
    land_title_type = models.CharField(max_length=100, blank=True)
    owner_name = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    land_size = models.CharField(max_length=100, blank=True)
    photo_url = models.URLField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'building_surveys'
        ordering = ['kobo_id']

    def __str__(self):
        return f'{self.proposed_auto_number} {self.proposed_street_name} ({self.locality})'
