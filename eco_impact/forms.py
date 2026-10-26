from django import forms
from .models import ImpactLog


class ImpactLogForm(forms.ModelForm):
    class Meta:
        model = ImpactLog
        # hanya field yang boleh diisi user secara manual
        fields = ['food_name', 'quantity', 'original_price', 'discounted_price', 'notes']
        widgets = {
            'food_name': forms.TextInput(attrs={'placeholder': 'Nama makanan yang diselamatkan'}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'original_price': forms.NumberInput(attrs={'placeholder': 'Harga normal (Rp)'}),
            'discounted_price': forms.NumberInput(attrs={'placeholder': 'Harga yang kamu bayar (Rp)'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Catatan tambahan (opsional)'}),
        }
        labels = {
            'food_name': 'Nama Makanan',
            'quantity': 'Jumlah',
            'original_price': 'Harga Normal (Rp)',
            'discounted_price': 'Harga Diskon (Rp)',
            'notes': 'Catatan',
        }