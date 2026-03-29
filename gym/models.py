from django.db import models
from django.contrib.auth.models import User


class MembershipPlan(models.Model):
    DEFAULT_TABS = ['dashboard', 'checklist', 'booking', 'diet', 'workout', 'global_workout', 'progress', 'bmi', 'nutrient', 'payments', 'profile']
    
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    features = models.JSONField(default=list)  # list of feature strings
    allowed_tabs = models.JSONField(default=list, blank=True)
    image_url = models.URLField(blank=True)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - NPR {self.price}"

    class Meta:
        ordering = ['price']


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    payment_ref = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan}"

    @property
    def days_remaining(self):
        from django.utils import timezone
        delta = self.end_date - timezone.now().date()
        return delta.days

    @property
    def is_expiring_soon(self):
        return 0 < self.days_remaining <= 7

    @property
    def is_expired(self):
        return self.days_remaining <= 0

    class Meta:
        ordering = ['-created_at']


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    image_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class GalleryImage(models.Model):
    image_url = models.URLField()
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
