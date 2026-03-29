from django.db import models
from django.contrib.auth.models import User


class AvailableSlot(models.Model):
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='available_slots',
        limit_choices_to={'profile__role': 'staff'}
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=1)
    title = models.CharField(max_length=100, blank=True)  # e.g. "Morning Yoga"
    color = models.CharField(max_length=20, default='#0d9488')  # for FullCalendar

    def __str__(self):
        return f"{self.instructor.email} - {self.date} {self.start_time}"

    @property
    def bookings_count(self):
        return self.bookings.filter(status='confirmed').count()

    @property
    def is_full(self):
        return self.bookings_count >= self.capacity

    @property
    def spots_left(self):
        return self.capacity - self.bookings_count

    class Meta:
        ordering = ['date', 'start_time']


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(AvailableSlot, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    booked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member.email} - {self.slot}"

    class Meta:
        unique_together = ('member', 'slot')
        ordering = ['-booked_at']


