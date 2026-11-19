from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


def _first_error(errors):
    """Ambil satu pesan error yang enak ditampilkan di SnackBar/Dialog Flutter."""
    if isinstance(errors, dict):
        for value in errors.values():
            return _first_error(value)
    if isinstance(errors, (list, tuple)) and errors:
        return _first_error(errors[0])
    return str(errors) if errors else "Data tidak valid."


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """Health check + daftar endpoint. Buka /api/ di browser untuk cek API hidup."""
    return Response(
        {
            "name": "LastBite API",
            "status": "ok",
            "endpoints": {
                "login": reverse("api:login", request=request, format=format),
                "register": reverse("api:register", request=request, format=format),
                "logout": reverse("api:logout", request=request, format=format),
                "me": reverse("api:me", request=request, format=format),
                "surprise_bags": reverse("api:surprise-bags", request=request, format=format),
                "orders": reverse("api:orders", request=request, format=format),
                "merchant_stores": reverse("api:merchant-stores", request=request, format=format),
                "food_hacks": reverse("api:food-hacks", request=request, format=format),
                "verified_reviews": reverse("api:verified-reviews", request=request, format=format),
                "impact_logs": reverse("api:impact-logs", request=request, format=format),
            },
        }
    )


class LoginView(APIView):
    """
    POST /api/auth/login/  (form-data atau JSON: username, password)
    Dipanggil dari Flutter dengan `request.login(url, {...})` (pbp_django_auth).
    Status 200 = berhasil (pbp_django_auth men-set request.loggedIn = true).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": False, "message": "Username dan password wajib diisi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"status": False, "message": "Username atau password salah."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response(
            {
                "status": True,
                "message": "Login berhasil!",
                **UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    POST /api/auth/register/  (JSON atau form-data)
    Wajib: username, password1, password2
    Opsional: nama_lengkap, email, role ("customer" [default] / "merchant")
    Dipanggil dari Flutter dengan `request.postJson(url, jsonEncode({...}))`.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": False,
                    "message": _first_error(serializer.errors),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        return Response(
            {
                "status": True,
                "message": "Akun berhasil dibuat! Silakan login.",
                **UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Dipanggil dari Flutter dengan `request.logout(url)`.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.user.username if request.user.is_authenticated else None
        logout(request)
        return Response(
            {"status": True, "message": "Logout berhasil!", "username": username},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    Dipakai Flutter saat app dibuka untuk cek apakah session lama masih valid.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "status": True,
                    "is_authenticated": True,
                    **UserSerializer(request.user).data,
                }
            )
        return Response({"status": False, "is_authenticated": False})
