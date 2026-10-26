import uuid

from django import forms


class OrderForm(forms.Form):
    quantity = forms.IntegerField(label='Jumlah paket', min_value=1, max_value=100,
                                  initial=1, widget=forms.NumberInput(attrs={'min': 1, 'max': 100}))
    reservation_key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)


class PickupVerificationForm(forms.Form):
    pickup_code = forms.RegexField(
        label='Kode pickup customer', regex=r'^[A-Fa-f0-9]{8}$', max_length=8, min_length=8,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'maxlength': 8}),
    )

    def clean_pickup_code(self):
        return self.cleaned_data['pickup_code'].upper()
