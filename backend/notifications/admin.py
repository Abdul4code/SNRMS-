from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('title', 'recipient', 'notification_type', 'application', 'is_read', 'created_at')
	list_filter = ('notification_type', 'is_read', 'created_at')
	search_fields = ('title', 'message', 'recipient__email', 'application__reference_number')
	readonly_fields = ('id', 'created_at', 'read_at')
