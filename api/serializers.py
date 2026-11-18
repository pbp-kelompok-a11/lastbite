from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.forms import RegistrationForm
from accounts.models import UserProfile

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class RegisterSerializer(serializers.Serializer):
    """
    Register dari aplikasi mobile. Validasi & penyimpanan memakai
    RegistrationForm milik website (app accounts), jadi aturannya sama persis:
    validator password, cek username, dan UserProfile + role ikut dibuat.
    """

    username = serializers.CharField(max_length=150)
    password1 = serializers.CharField(trim_whitespace=False)
    password2 = serializers.CharField(trim_whitespace=False)
    nama_lengkap = serializers.CharField(required=False, allow_blank=True, default='')
    email = serializers.CharField(required=False, allow_blank=True, default='')
    role = serializers.ChoiceField(
        choices=UserProfile.Role.choices,
        required=False,
        default=UserProfile.Role.CUSTOMER,
    )

    def validate(self, attrs):
        form = RegistrationForm(data=attrs)
        if not form.is_valid():
            raise serializers.ValidationError(
                {field: list(errors) for field, errors in form.errors.items()}
            )
        self._form = form
        return attrs

    def create(self, validated_data):
        return self._form.save()


class UserSerializer(serializers.ModelSerializer):
    nama_lengkap = serializers.CharField(source='first_name', read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'nama_lengkap', 'email', 'role']

    def get_role(self, user):
        profile = getattr(user, 'profile', None)
        return profile.role if profile else None
