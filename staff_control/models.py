from django.db import models
from django.contrib.auth.models import User


# All available staff feature keys
FEATURE_CHOICES = [
    ('my_schedule', 'My Schedule (Calendar)'),
    ('my_members', 'My Members'),
    ('diet_plans', 'Diet Plans'),
    ('workout_plans', 'Workout Plans'),
    ('global_workout', 'Workout Library'),
    ('progress', 'Member Progress'),
]

ALL_FEATURE_KEYS = [f[0] for f in FEATURE_CHOICES]


class StaffPermission(models.Model):
    staff_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='staff_permissions'
    )
    # Stored as JSON list of feature keys, e.g. ["my_schedule", "my_members"]
    allowed_nav = models.JSONField(default=list)

    def __str__(self):
        return f"Permissions for {self.staff_user.email}"

    def has_permission(self, feature_key):
        return feature_key in self.allowed_nav

    def get_allowed_features(self):
        return self.allowed_nav

    @classmethod
    def get_or_create_for_staff(cls, user):
        obj, created = cls.objects.get_or_create(
            staff_user=user,
            defaults={'allowed_nav': ALL_FEATURE_KEYS}
        )
        return obj
