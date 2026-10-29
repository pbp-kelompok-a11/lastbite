from django import forms
from .models import ImpactLog


class ImpactLogForm(forms.ModelForm):
    class Meta:
        model = ImpactLog
        # Field yang diisi customer untuk pencatatan manual
        fields = ['food_name', 'notes', 'quantity', 'original_price', 'discounted_price']
        widgets = {
            'food_name': forms.TextInput(attrs={'placeholder': 'Contoh: Croissant Almond, Nasi Bento, dll.'}),
            'notes': forms.TextInput(attrs={'placeholder': 'Contoh: Bakers Corner, Toko Roti Barokah, dll.'}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'original_price': forms.NumberInput(attrs={'placeholder': 'Harga normal (Rp)'}),
            'discounted_price': forms.NumberInput(attrs={'placeholder': 'Harga yang kamu bayar (Rp)'}),
        }
        labels = {
            'food_name': 'Nama Makanan',
            'notes': 'Nama Toko / Tempat Penyelamatan',
            'quantity': 'Jumlah (Porsi)',
            'original_price': 'Harga Normal (Rp)',
            'discounted_price': 'Harga Diskon (Rp)',
        }
