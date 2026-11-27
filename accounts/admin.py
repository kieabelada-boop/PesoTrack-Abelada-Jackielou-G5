from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'business_name', 'contact_number', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Store & Role Profile', {"fields": ('role', 'business_name', 'contact_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Store & Role Profile', {"fields": ('role', 'business_name', 'contact_number')}),
    )
