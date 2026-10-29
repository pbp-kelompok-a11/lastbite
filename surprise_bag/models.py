import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.urls import reverse


class SurpriseBag(models.Model):
    CATEGORY_CHOICES = [
        ('bakery', 'Bakery & Pastry'),
        ('meal', 'Nasi & Lauk'),
        ('snack', 'Snack & Jajanan'),
        ('dessert', 'Dessert & Kue'),
        ('beverage', 'Minuman'),
        ('mixed', 'Campuran'),
    ]

    # emoji dipakai sebagai visual kartu, biar nggak perlu upload gambar
    CATEGORY_EMOJI = {
        'bakery': '🥐',
        'meal': '🍱',
        'snack': '🥪',
        'dessert': '🍰',
        'beverage': '🧋',
        'mixed': '🛍️',
    }

    distance_km = None

    # uuid biar id-nya unik dan aman dipakai di URL
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # pemilik paket — hanya user ini yang boleh mengubah/menghapus
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surprise_bags')

    name = models.CharField(max_length=100)
    description = models.TextField()
    # link gambar (opsional); kalau kosong, kartu pakai emoji kategori
    image_url = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='mixed')

    original_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('1'))]
    )
    discounted_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    stock = models.PositiveIntegerField(default=1)

    pickup_start = models.TimeField()
    pickup_end = models.TimeField()

    # dipakai untuk "menonaktifkan" penawaran tanpa menghapus datanya
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # yang terbaru muncul duluan

    def __str__(self):
        return f"{self.name} — {self.merchant.username}"

    def get_absolute_url(self):
        return reverse('surprise_bag:detail', args=[self.pk])

    def clean(self):
        errors = {}
        if (self.original_price is not None and self.discounted_price is not None
                and self.discounted_price >= self.original_price):
            errors['discounted_price'] = 'Harga diskon harus lebih murah dari harga normal.'
        if self.pickup_start and self.pickup_end and self.pickup_end <= self.pickup_start:
            errors['pickup_end'] = 'Jam selesai pickup harus setelah jam mulai.'
        if errors:
            raise ValidationError(errors)

    @property
    def discount_percent(self):
        if not self.original_price:
            return 0
        return round((1 - self.discounted_price / self.original_price) * 100)

    @property
    def is_available(self):
        return self.is_active and self.stock > 0

    @property
    def emoji(self):
        return self.CATEGORY_EMOJI.get(self.category, '🛍️')

    @property
    def merchant_name(self):
        # utamakan nama toko dari Modul Merchant Store; kalau belum dibuat, pakai nama akun
        store = getattr(self.merchant, 'merchant_store', None)
        if store is not None:
            return store.name
        return self.merchant.get_full_name() or self.merchant.username


    @property
    def pickup_time(self):
        return f"{self.pickup_start:%H:%M}–{self.pickup_end:%H:%M}"

    def reduce_stock(self, quantity=1):
        """Dipanggil Modul Order saat pesanan dibuat. Atomic, jadi aman dari race condition."""
        updated = SurpriseBag.objects.filter(
            pk=self.pk, is_active=True, stock__gte=quantity
        ).update(stock=F('stock') - quantity)
        if updated:
            self.refresh_from_db(fields=['stock'])
        return bool(updated)

    def to_dict(self):
        # format JSON untuk endpoint AJAX
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'category_label': self.get_category_display(),
            'emoji': self.emoji,
            'image_url': self.image_url,
            'merchant': self.merchant_name,
            'original_price': float(self.original_price),
            'discounted_price': float(self.discounted_price),
            'discount_percent': self.discount_percent,
            'stock': self.stock,
            'pickup_start': self.pickup_start.strftime('%H:%M'),
            'pickup_end': self.pickup_end.strftime('%H:%M'),
            'is_active': self.is_active,
            'is_available': self.is_available,
            'detail_url': self.get_absolute_url(),
        }


class BagWishlist(models.Model):
    """Relasi Surprise Bag favorit (wishlist) milik seorang Customer — konsepnya sama dengan StoreWishlist."""

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bag_wishlist_items')
    bag = models.ForeignKey(SurpriseBag, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['customer', 'bag'], name='surprise_bag_unique_wishlist'),
        ]

    def __str__(self):
        return f'{self.customer.get_username()} ♥ {self.bag.name}'

    @classmethod
    def bag_ids_for(cls, user):
        """ID Surprise Bag yang ada di wishlist user (kosong untuk guest)."""
        if not user.is_authenticated:
            return set()
        return set(cls.objects.filter(customer=user).values_list('bag_id', flat=True))
