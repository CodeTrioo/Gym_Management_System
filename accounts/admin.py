from django.contrib import admin
from accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'speciality', 'joined_date']
    list_filter = ['role']
    search_fields = ['user__email', 'phone', 'speciality']
