from django import forms
from .models import SurpriseBag

MIN_DISCOUNT = 30
MAX_DISCOUNT = 50


class DiscountRangeMixin:
    """Validasi diskon 30–50% sesuai konsep LastBite."""

    def clean(self):
        cleaned = super().clean()
        # di form update, harga normal tidak ada di form, jadi ambil dari instance
        original = cleaned.get('original_price', self.instance.original_price)
        discounted = cleaned.get('discounted_price')
        if original and discounted is not None and discounted < original:
            percent = (1 - discounted / original) * 100
            if not MIN_DISCOUNT <= percent <= MAX_DISCOUNT:
                self.add_error(
                    'discounted_price',
                    f'Diskon harus di antara {MIN_DISCOUNT}–{MAX_DISCOUNT}% (sekarang {percent:.0f}%).',
                )
        return cleaned


class SurpriseBagForm(DiscountRangeMixin, forms.ModelForm):
    class Meta:
        model = SurpriseBag
        fields = [
            'name', 'description', 'category', 'image_url', 'original_price', 'discounted_price',
            'stock', 'pickup_start', 'pickup_end', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contoh: Paket Roti Manis Sore'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Isi paket kira-kira apa saja?'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'original_price': forms.NumberInput(attrs={'min': 0, 'step': 100, 'placeholder': 'Harga normal (Rp)'}),
            'discounted_price': forms.NumberInput(attrs={'min': 0, 'step': 100, 'placeholder': 'Harga jual (Rp)'}),
            'stock': forms.NumberInput(attrs={'min': 0}),
            'pickup_start': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'pickup_end': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }
        labels = {
            'name': 'Nama Paket',
            'description': 'Deskripsi',
            'image_url': 'Link Gambar (opsional)',
            'category': 'Kategori',
            'original_price': 'Harga Normal (Rp)',
            'discounted_price': 'Harga Diskon (Rp)',
            'stock': 'Kuota Stok',
            'pickup_start': 'Pickup Mulai',
            'pickup_end': 'Pickup Selesai',
            'is_active': 'Tampilkan di katalog',
        }


class SurpriseBagUpdateForm(SurpriseBagForm):
    # sesuai README: yang boleh diubah hanya harga diskon, stok, dan jam pickup
    class Meta(SurpriseBagForm.Meta):
        fields = ['image_url', 'discounted_price', 'stock', 'pickup_start', 'pickup_end', 'is_active']
