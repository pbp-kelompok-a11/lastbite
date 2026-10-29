from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserProfile
from .permissions import is_customer, is_merchant


class AccountsTests(TestCase):
    def test_profile_updates_only_current_users_personal_fields(self):
        user = get_user_model().objects.create_user(username='profile_owner', password='LastBite-Test-937!')
        UserProfile.objects.create(user=user, role='customer')
        other = get_user_model().objects.create_user(username='profile_other')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_details', 'username': 'updated_owner',
            'full_name': 'Nadia Putri', 'email': 'nadia@example.com',
            'current_password': 'LastBite-Test-937!',
            'id': other.pk, 'role': 'merchant', 'is_staff': True,
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        user.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(user.username, 'updated_owner')
        self.assertEqual(user.get_full_name(), 'Nadia Putri')
        self.assertEqual(user.last_name, '')
        self.assertEqual(user.email, 'nadia@example.com')
        self.assertEqual(user.profile.role, 'customer')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('LastBite-Test-937!'))
        self.assertEqual(other.username, 'profile_other')

    def test_invalid_profile_preserves_saved_details_and_shows_errors(self):
        user = get_user_model().objects.create_user(
            username='profile_owner', first_name='Nadia', password='LastBite-Test-937!',
        )
        UserProfile.objects.create(user=user, role='customer')
        get_user_model().objects.create_user(username='profile_taken')
        self.client.force_login(user)
        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_details', 'username': 'profile_taken',
            'full_name': 'Changed', 'email': 'invalid-email',
            'current_password': 'LastBite-Test-937!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['profile_form'].errors)
        self.assertIn('email', response.context['profile_form'].errors)
        user.refresh_from_db()
        self.assertEqual(user.username, 'profile_owner')
        self.assertEqual(user.first_name, 'Nadia')

    def test_profile_edit_requires_correct_password(self):
        user = get_user_model().objects.create_user(username='protected_profile', password='LastBite-Test-937!')
        UserProfile.objects.create(user=user, role='customer')
        self.client.force_login(user)
        for password in ('', 'wrong-password'):
            response = self.client.post(reverse('accounts:profile'), {
                'action': 'update_details', 'username': 'changed_profile',
                'full_name': 'Changed', 'email': '', 'current_password': password,
            })
            self.assertIn('current_password', response.context['profile_form'].errors)
            self.assertEqual(response.context['open_dialog'], 'profile-edit-dialog')
            user.refresh_from_db()
            self.assertEqual(user.username, 'protected_profile')
            self.assertNotContains(response, 'value="wrong-password"')

    def test_change_password_validates_and_keeps_current_session(self):
        user = get_user_model().objects.create_user(username='password_owner', password='LastBite-Test-937!')
        UserProfile.objects.create(user=user, role='customer')
        self.client.force_login(user)
        base = {
            'action': 'change_password', 'password-old_password': 'LastBite-Test-937!',
            'password-new_password1': 'Fresh-LastBite-8492!',
            'password-new_password2': 'Fresh-LastBite-8492!',
        }
        for changes, field in (
            ({'password-old_password': 'wrong'}, 'old_password'),
            ({'password-new_password2': 'mismatch'}, 'new_password2'),
            ({'password-new_password1': '123', 'password-new_password2': '123'}, 'new_password2'),
        ):
            response = self.client.post(reverse('accounts:profile'), {**base, **changes})
            self.assertIn(field, response.context['password_form'].errors)
            self.assertEqual(response.context['open_dialog'], 'profile-password-dialog')
            user.refresh_from_db()
            self.assertTrue(user.check_password('LastBite-Test-937!'))
            self.assertNotContains(response, 'value="Fresh-LastBite-8492!"')
        self.assertRedirects(self.client.post(reverse('accounts:profile'), base), reverse('accounts:profile'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('Fresh-LastBite-8492!'))
        self.assertFalse(user.check_password('LastBite-Test-937!'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_profile_requires_login_and_explains_merchant_setup(self):
        url = reverse('accounts:profile')
        self.assertRedirects(self.client.get(url), reverse('accounts:login') + '?next=' + url)
        user = get_user_model().objects.create_user(username='profile_merchant')
        UserProfile.objects.create(user=user, role='merchant')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertContains(response, 'Lengkapi Profil Toko')
        self.assertContains(response, reverse('merchant_store:create'))

    def registration_data(self, **changes):
        data = {'username': 'newuser', 'role': 'customer',
                'password1': 'LastBite-Test-937!', 'password2': 'LastBite-Test-937!'}
        data.update(changes)
        return data

    def test_register_both_roles_and_hash_passwords(self):
        for role in ('customer', 'merchant'):
            response = self.client.post(reverse('accounts:register'), self.registration_data(
                username=role, role=role, is_staff=True, is_superuser=True,
            ))
            self.assertRedirects(response, reverse('accounts:login'))
            user = get_user_model().objects.get(username=role)
            self.assertEqual(user.profile.role, role)
            self.assertTrue(user.check_password('LastBite-Test-937!'))
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)

    def test_invalid_registration_does_not_save_user_or_profile(self):
        initial_users = get_user_model().objects.count()
        initial_profiles = UserProfile.objects.count()
        for changes in ({'role': 'admin'}, {'password2': 'wrong'}, {'password1': '123', 'password2': '123'}, {'username': ''}):
            with self.subTest(changes=changes):
                response = self.client.post(reverse('accounts:register'), self.registration_data(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertEqual(get_user_model().objects.count(), initial_users)
                self.assertEqual(UserProfile.objects.count(), initial_profiles)

    def test_duplicate_username_rejected(self):
        initial_users = get_user_model().objects.count()
        self.client.post(reverse('accounts:register'), self.registration_data())
        response = self.client.post(reverse('accounts:register'), self.registration_data())
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), initial_users + 1)

    def test_login_session_and_post_logout(self):
        user = get_user_model().objects.create_user(username='customer', password='LastBite-Test-937!')
        UserProfile.objects.create(user=user, role='customer')
        response = self.client.post(reverse('accounts:login'), {'username': 'customer', 'password': 'LastBite-Test-937!'})
        self.assertRedirects(response, reverse('main:home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertContains(self.client.get(reverse('main:home')), reverse('accounts:profile'))
        self.assertEqual(user.profile.role, 'customer')
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('main:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_bad_login_rejected(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'missing', 'password': 'bad'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registration_success_notification_shows_once(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(), follow=True)
        self.assertContains(response, 'Akun berhasil dibuat. Silakan login.', count=1)
        self.assertContains(response, 'notification--success')
        self.assertNotContains(self.client.get(reverse('accounts:login')), 'Akun berhasil dibuat. Silakan login.')

    def test_login_success_notification_on_destination(self):
        get_user_model().objects.create_user(username='welcome_user', password='LastBite-Test-937!')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'welcome_user', 'password': 'LastBite-Test-937!',
        }, follow=True)
        self.assertContains(response, 'Selamat datang kembali, welcome_user!', count=1)
        self.assertContains(response, 'Tutup notifikasi')
        self.assertNotContains(self.client.get(reverse('main:home')), 'Selamat datang kembali, welcome_user!')

    def test_logout_confirmation_and_cancel_keep_session(self):
        user = get_user_model().objects.create_user(username='confirm_user')
        url = reverse('main:home')
        self.assertNotContains(self.client.get(url), 'id="logout-dialog"')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="logout-dialog"')
        self.assertContains(response, 'Anda yakin ingin logout?')
        self.assertContains(response, 'action="{}"'.format(reverse('accounts:logout')))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.client.get(reverse('main:home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(user)
        self.assertEqual(secure_client.post(reverse('accounts:logout')).status_code, 403)
        self.assertIn('_auth_user_id', secure_client.session)

    def test_safe_next_and_external_redirect_rejection(self):
        get_user_model().objects.create_user(username='customer', password='LastBite-Test-937!')
        for next_url, expected in (('/accounts/register/', '/accounts/register/'), ('https://example.org/', '/')):
            self.client.logout()
            response = self.client.post(reverse('accounts:login'), {
                'username': 'customer', 'password': 'LastBite-Test-937!', 'next': next_url,
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, expected)

    def test_role_helpers_deny_guests_and_accounts_without_profile(self):
        user = get_user_model().objects.create_user(username='legacy')
        for actor in (AnonymousUser(), user):
            self.assertFalse(is_customer(actor))
            self.assertFalse(is_merchant(actor))
        UserProfile.objects.create(user=user, role='merchant')
        user.refresh_from_db()
        self.assertTrue(is_merchant(user))
        self.assertFalse(is_customer(user))

    def test_pages_and_csrf(self):
        for name in ('register', 'login'):
            response = self.client.get(reverse('accounts:' + name))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'accounts/' + name + '.html')
            self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('accounts:' + name), {}).status_code, 403)

    def test_merchant_registration_link_preselects_role(self):
        response = self.client.get(reverse('accounts:register'), {'role': 'merchant'})
        self.assertEqual(response.context['form'].initial['role'], 'merchant')
        response = self.client.get(reverse('accounts:register'), {'role': 'admin'})
        self.assertEqual(response.context['form'].initial['role'], 'customer')

    def test_authenticated_user_cannot_register_another_account(self):
        user = get_user_model().objects.create_user(username='existing')
        initial_users = get_user_model().objects.count()
        self.client.force_login(user)
        self.assertRedirects(self.client.post(reverse('accounts:register'), self.registration_data()), reverse('main:home'))
        self.assertEqual(get_user_model().objects.count(), initial_users)
