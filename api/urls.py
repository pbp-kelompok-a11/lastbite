"""
URL dasar API untuk aplikasi Flutter. Di urls.py proyek:

    path("api/", include("api.urls")),

Endpoint modul sebaiknya tinggal di app modul masing-masing (serializer +
viewset di app itu sendiri), lalu didaftarkan di urls.py proyek, misalnya:

    path("api/merchant/", include("merchant_store.api_urls")),
"""

from django.urls import path

from .views import LoginView, LogoutView, MeView, RegisterView, api_root

app_name = "api"

urlpatterns = [
    path("", api_root, name="root"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
]
