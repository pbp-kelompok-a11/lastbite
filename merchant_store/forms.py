import re

from django import forms

from .models import MerchantStore

PHONE_RE = re.compile(r'^\+?[0-9][0-9\s\-]{7,18}$')


class MerchantStoreForm(forms.ModelForm):
    class Meta:
        model = MerchantStore
        fields = [
            'name', 'description', 'address', 'phone',
            'business_email', 'opening_time', 'closing_time',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contoh: Bakers Corner UI'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ceritakan singkat tentang tokomu (opsional)'}),
            'address': forms.TextInput(attrs={
                'placeholder': 'Contoh: Jl. Margonda Raya No. 100, Pondok Cina, Depok',
            }),
            'phone': forms.TextInput(attrs={'placeholder': '081234567890', 'inputmode': 'tel'}),
            'business_email': forms.EmailInput(attrs={'placeholder': 'toko@contoh.com (opsional)'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }
        help_texts = {
            'address': 'Tulis selengkap mungkin (jalan, kelurahan, kota). Koordinat peta dicari otomatis dari alamat ini.',
        }

    def clean_name(self):
        name = ' '.join(self.cleaned_data['name'].split())
        if len(name) < 3:
            raise forms.ValidationError('Nama gerai minimal 3 karakter.')
        return name

    def clean_address(self):
        address = ' '.join(self.cleaned_data['address'].split())
        if len(address) < 10:
            raise forms.ValidationError('Alamat terlalu pendek. Tulis alamat selengkap mungkin.')
        return address

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError('Nomor telepon tidak valid. Gunakan angka, contoh: 081234567890.')
        return phone

    def clean(self):
        cleaned = super().clean()
        opening, closing = cleaned.get('opening_time'), cleaned.get('closing_time')
        if opening and closing and opening == closing:
            self.add_error('closing_time', 'Jam tutup tidak boleh sama dengan jam buka.')
        return cleaned
