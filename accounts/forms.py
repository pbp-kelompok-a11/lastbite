from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import UserProfile


class RegistrationForm(UserCreationForm):
    nama_lengkap = forms.CharField(label='Nama lengkap', required=False)
    email = forms.EmailField(label='Email', required=False)
    role = forms.ChoiceField(label='Daftar sebagai', choices=UserProfile.Role.choices, initial='customer', required=False)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'nama_lengkap', 'email', 'role']

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        nama = self.cleaned_data.get('nama_lengkap', '').strip()
        if nama:
            user.first_name = nama
        email = self.cleaned_data.get('email', '').strip()
        if email:
            user.email = email
        if commit:
            user.save()
            role = self.cleaned_data.get('role') or 'customer'
            UserProfile.objects.create(user=user, role=role)
        return user
