from django.contrib import admin
from gym.models import MembershipPlan, Enrollment, Announcement, GalleryImage

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'is_popular', 'is_active']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active']

admin.site.register(GalleryImage)
