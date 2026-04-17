from django.contrib import admin
from .models import Application, StatusHistory


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
	list_display = (
		'reference_number',
		'proposed_street_name',
		'applicant',
		'street_type',
		'ward',
		'status',
		'created_at',
	)
	list_filter = ('status', 'ward', 'street_type', 'created_at', 'is_deleted')
	search_fields = ('reference_number', 'proposed_street_name', 'applicant__email', 'certificate_number')
	readonly_fields = ('id', 'reference_number', 'created_at', 'updated_at')


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
	list_display = (
		'application',
		'from_status',
		'to_status',
		'changed_by',
		'created_at',
	)
	list_filter = ('from_status', 'to_status', 'created_at')
	search_fields = ('application__reference_number', 'changed_by__email', 'remarks')
	readonly_fields = ('id', 'created_at')
