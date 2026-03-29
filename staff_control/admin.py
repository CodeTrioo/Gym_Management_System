from django.contrib import admin
from staff_control.models import StaffPermission

@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    list_display = ['staff_user', 'allowed_nav']
