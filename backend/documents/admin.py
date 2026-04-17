from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
	list_display = (
		'application',
		'document_type',
		'uploaded_by',
		'is_verified',
		'is_deleted',
		'created_at',
	)
	list_filter = ('document_type', 'is_verified', 'is_deleted', 'created_at')
	search_fields = (
		'application__reference_number',
		'original_filename',
		'uploaded_by__email',
		'mime_type',
	)
	readonly_fields = ('id', 'file_size', 'created_at')
