from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class ImpactLog(models.Model):
    # dua jenis log: otomatis dari order, atau manual dari user
    SOURCE_CHOICES = [
        ('order', 'Order (Otomatis)'),
        ('manual', 'Manual'),
    ]

    # uuid biar id-nya unik dan aman dipakai di URL
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='impact_logs')

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    # order_id diisi nanti kalau modul Order sudah ready, sekarang boleh kosong
    order_id = models.UUIDField(null=True, blank=True)

    food_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)

    # dua harga ini yang kita pakai buat ngitung selisih penghematan
    original_price = models.DecimalField(max_digits=12, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2)

    notes = models.TextField(blank=True, default='')  # catatan opsional dari user

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  # auto update tiap kali save

    class Meta:
        ordering = ['-created_at']  # yang terbaru muncul duluan

    def __str__(self):
        return f"{self.user.username} — {self.food_name} ({self.created_at.date()})"

    # kalkulasi penghematan: selisih harga dikali jumlah item
    @property
    def money_saved(self):
        return (self.original_price - self.discounted_price) * self.quantity

    # estimasi karbon pakai faktor emisi rata-rata food waste Indonesia
    # asumsi: 1 porsi ≈ 0.3 kg, faktor emisi 2.5 kg CO2 per kg makanan terbuang
    @property
    def carbon_prevented_kg(self):
        EMISSION_FACTOR = 2.5
        AVG_FOOD_WEIGHT_KG = 0.3
        return round(self.quantity * AVG_FOOD_WEIGHT_KG * EMISSION_FACTOR, 2)