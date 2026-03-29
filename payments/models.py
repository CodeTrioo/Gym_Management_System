from django.db import models
from django.contrib.auth.models import User


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    product_code = models.CharField(max_length=100)
    transaction_uuid = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    esewa_ref_id = models.CharField(max_length=200, blank=True)
    enrollment = models.ForeignKey(
        'gym.Enrollment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transactions'
    )
    plan = models.ForeignKey(
        'gym.MembershipPlan', on_delete=models.SET_NULL,
        null=True, related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - NPR {self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']
