from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class MerchantStore(models.Model):
    """Profil toko fisik milik satu Merchant (satu merchant = satu toko)."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchant_store',
    )
    name = models.CharField('nama gerai', max_length=120)
    description = models.TextField('deskripsi', blank=True)
    address = models.CharField('alamat lengkap', max_length=255)
    phone = models.CharField('nomor telepon', max_length=20)
    business_email = models.EmailField('email bisnis', blank=True)
    opening_time = models.TimeField('jam buka')
    closing_time = models.TimeField('jam tutup')

    # Diisi otomatis dari OpenStreetMap Nominatim (lihat services.geocode_address)
    latitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    is_active = models.BooleanField('aktif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    def is_open_now(self):
        """True jika sekarang (waktu Asia/Jakarta) berada dalam jam operasional."""
        now = timezone.localtime(timezone.now()).time()
        opening, closing = self.opening_time, self.closing_time
        if opening <= closing:
            return opening <= now <= closing
        # jam operasional melewati tengah malam, mis. 18:00 - 02:00
        return now >= opening or now <= closing

    @property
    def hours_display(self):
        return f'{self.opening_time:%H:%M} - {self.closing_time:%H:%M}'


class StoreWishlist(models.Model):
    """Relasi toko favorit (wishlist) milik seorang Customer."""

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    store = models.ForeignKey(
        MerchantStore,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'store'], name='merchant_store_unique_wishlist',
            ),
        ]

    def __str__(self):
        return f'{self.customer.get_username()} ♥ {self.store.name}'
