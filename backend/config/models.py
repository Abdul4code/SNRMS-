import uuid
from django.db import models


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
