from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.db import transaction

from .models import UserProfile


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        label='Nama lengkap', max_length=150, required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'name'}),
    )
    current_password = forms.CharField(
        label='Password saat ini', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    class Meta:
        model = get_user_model()
        fields = ['full_name', 'username', 'email', 'current_password']
        labels = {
            'username': 'Username',
            'email': 'Email',
        }
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['full_name'] = self.instance.get_full_name()

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.instance.check_password(password):
            raise forms.ValidationError('Password saat ini tidak benar.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['full_name']
        user.last_name = ''
        if commit:
            user.save()
        return user


class ProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Password lama'
        self.fields['new_password1'].label = 'Password baru'
        self.fields['new_password2'].label = 'Konfirmasi password baru'


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
