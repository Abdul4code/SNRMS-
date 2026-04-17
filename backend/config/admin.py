from django.contrib import admin
from .models import BuildingSurvey, FeeConfiguration, StreetType


@admin.register(StreetType)
class StreetTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'code', 'is_active', 'created_at')
	list_filter = ('is_active', 'created_at')
	search_fields = ('name', 'code')
	readonly_fields = ('id', 'created_at')


@admin.register(FeeConfiguration)
class FeeConfigurationAdmin(admin.ModelAdmin):
	list_display = ('component', 'street_type', 'amount', 'is_active', 'updated_by', 'updated_at')
	list_filter = ('component', 'is_active', 'updated_at')
	search_fields = ('component', 'street_type__name', 'updated_by__email')
	readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(BuildingSurvey)
class BuildingSurveyAdmin(admin.ModelAdmin):
	list_display = ('kobo_id', 'proposed_auto_number', 'proposed_street_name', 'locality', 'ward', 'survey_date')
	list_filter = ('building_use', 'building_type', 'occupancy_type', 'ward', 'survey_date')
	search_fields = (
		'kobo_id',
		'proposed_auto_number',
		'proposed_street_name',
		'existing_street_name',
		'owner_name',
		'contact_number',
		'locality',
	)
	readonly_fields = ('created_at',)
