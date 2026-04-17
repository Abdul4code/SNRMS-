from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = (
		'application',
		'stage',
		'status',
		'amount_expected',
		'amount_submitted',
		'payment_reference',
		'confirmed_by',
		'created_at',
	)
	list_filter = ('stage', 'status', 'bank_name', 'created_at', 'confirmed_at')
	search_fields = ('application__reference_number', 'payment_reference', 'bank_name', 'confirmed_by__email')
	readonly_fields = ('id', 'created_at', 'updated_at', 'submitted_at', 'confirmed_at')
