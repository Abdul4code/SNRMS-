from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	ordering = ('-created_at',)
	list_display = (
		'email',
		'first_name',
		'last_name',
		'role',
		'is_staff',
		'is_superuser',
		'is_active',
		'created_at',
	)
	list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'created_at')
	search_fields = ('email', 'first_name', 'last_name', 'phone')
	readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')

	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'role')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
	)

	add_fieldsets = (
		(
			None,
			{
				'classes': ('wide',),
				'fields': ('email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active'),
			},
		),
	)
