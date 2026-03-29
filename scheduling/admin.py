from django.contrib import admin
from scheduling.models import AvailableSlot, Booking

@admin.register(AvailableSlot)
class AvailableSlotAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'date', 'start_time', 'end_time', 'capacity']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['member', 'slot', 'status', 'booked_at']
    list_filter = ['status']

