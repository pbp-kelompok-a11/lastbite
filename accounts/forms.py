from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import UserProfile


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(label='Daftar sebagai', choices=UserProfile.Role.choices)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'role']

    @transaction.atomic
    def save(self):
        user = super().save()
        UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user
