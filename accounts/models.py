from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('member', 'Member'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    phone = models.CharField(max_length=20, blank=True)
    profile_image_url = models.URLField(blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)  # for staff/instructors
    speciality = models.CharField(max_length=100, blank=True)  # for instructors
    instructor = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_members',
        limit_choices_to={'role': 'staff'}
    )
    joined_date = models.DateField(auto_now_add=True)
    target_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} ({self.role})"

    def get_profile_image(self):
        return self.profile_image_url or 'https://ui-avatars.com/api/?name=' + self.user.email + '&background=0d9488&color=fff'

    @property
    def active_plan_name(self):
        active_enrollment = self.user.enrollments.filter(is_active=True).first()
        return active_enrollment.plan.name if (active_enrollment and active_enrollment.plan) else "No Active Plan"