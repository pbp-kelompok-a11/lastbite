from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        MERCHANT = 'merchant', 'Merchant'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile',
    )
    role = models.CharField(max_length=10, choices=Role.choices)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=['customer', 'merchant']),
                name='accounts_profile_valid_role',
            ),
        ]

    def __str__(self):
        return f'{self.user.get_username()} ({self.get_role_display()})'
