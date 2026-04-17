from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ('action', 'entity_type', 'entity_id', 'actor', 'ip_address', 'created_at')
	list_filter = ('action', 'entity_type', 'created_at')
	search_fields = ('action', 'entity_type', 'entity_id', 'actor__email', 'description')
	readonly_fields = ('id', 'created_at')
