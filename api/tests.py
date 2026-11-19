from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from accounts.models import UserProfile

User = get_user_model()
STRONG_PASSWORD = "Lastbite#2026x"


class MobileAuthApiTests(APITestCase):
    """
    Mensimulasikan aplikasi Flutter: request dikirim TANPA token CSRF
    (enforce_csrf_checks=True), sama seperti pbp_django_auth.
    """

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def _create_user(self, username="tester", role=UserProfile.Role.CUSTOMER):
        user = User.objects.create_user(username=username, password=STRONG_PASSWORD)
        UserProfile.objects.create(user=user, role=role)
        return user

    def _login(self, username="tester", password=STRONG_PASSWORD):
        # pbp_django_auth.login() mengirim form-data, bukan JSON
        return self.client.post(
            "/api/auth/login/", {"username": username, "password": password}
        )

    def _register(self, fmt="json", **extra):
        data = {"username": "baru", "password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD}
        data.update(extra)
        if fmt == "json":
            return self.client.post("/api/auth/register/", data, format="json")
        return self.client.post("/api/auth/register/", data)

    def test_api_root_is_up(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_register_creates_customer_profile_by_default(self):
        response = self._register()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertEqual(body["role"], "customer")
        user = User.objects.get(username="baru")
        self.assertEqual(user.profile.role, "customer")

    def test_register_merchant_with_full_data(self):
        response = self._register(
            role="merchant", nama_lengkap="Toko Baru", email="toko@example.com"
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="baru")
        self.assertEqual(user.profile.role, "merchant")
        self.assertEqual(user.first_name, "Toko Baru")
        self.assertEqual(user.email, "toko@example.com")

    def test_register_with_form_data(self):
        response = self._register(fmt="form")
        self.assertEqual(response.status_code, 201)

    def test_register_invalid_role(self):
        response = self._register(role="admin")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="baru").exists())

    def test_register_password_mismatch(self):
        response = self._register(password2="beda123!xyz")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["status"])
        self.assertTrue(response.json()["message"])

    def test_register_duplicate_username(self):
        self._create_user("kembar")
        response = self._register(username="kembar")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["status"])

    def test_login_success_sets_session_cookie(self):
        self._create_user(role=UserProfile.Role.MERCHANT)
        response = self._login()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertEqual(body["username"], "tester")
        self.assertEqual(body["role"], "merchant")
        self.assertIn("sessionid", response.cookies)

    def test_login_wrong_password(self):
        self._create_user()
        response = self._login(password="salah")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["status"])

    def test_me_reflects_session(self):
        self._create_user()
        self.assertFalse(self.client.get("/api/auth/me/").json()["is_authenticated"])
        self._login()
        body = self.client.get("/api/auth/me/").json()
        self.assertTrue(body["is_authenticated"])
        self.assertEqual(body["username"], "tester")
        self.assertEqual(body["role"], "customer")

    def test_logout_without_csrf_token(self):
        """POST dari user yang sudah login tanpa X-CSRFToken harus tetap lolos."""
        self._create_user()
        self._login()
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["status"])
        self.assertFalse(self.client.get("/api/auth/me/").json()["is_authenticated"])
