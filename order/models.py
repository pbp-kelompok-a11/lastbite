import secrets
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def generate_pickup_code():
    return secrets.token_hex(4).upper()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY_TO_PICKUP = 'ready_to_pickup', 'Ready to Pickup'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    surprise_bag = models.ForeignKey('surprise_bag.SurpriseBag', on_delete=models.PROTECT, related_name='orders')
    # Snapshot menjaga transaksi lama saat harga atau jam paket diedit.
    food_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    original_price = models.DecimalField(max_digits=12, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2)
    pickup_date = models.DateField()
    pickup_start = models.TimeField()
    pickup_end = models.TimeField()
    pickup_code = models.CharField(max_length=8, default=generate_pickup_code, editable=False)
    reservation_key = models.UUIDField(unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='order_quantity_positive'),
            models.CheckConstraint(condition=models.Q(discounted_price__gte=0,
                                                      original_price__gte=models.F('discounted_price')),
                                   name='order_valid_prices'),
            models.CheckConstraint(condition=models.Q(status__in=['pending', 'ready_to_pickup', 'completed', 'cancelled']),
                                   name='order_valid_status'),
            models.CheckConstraint(condition=(models.Q(status='completed', completed_at__isnull=False)
                                              | (~models.Q(status='completed') & models.Q(completed_at__isnull=True))),
                                   name='order_completion_timestamp'),
        ]

    @property
    def total_price(self):
        return self.discounted_price * self.quantity

    @property
    def money_saved(self):
        return (self.original_price - self.discounted_price) * self.quantity

    def __str__(self):
        return f'{self.food_name} ({self.get_status_display()})'
