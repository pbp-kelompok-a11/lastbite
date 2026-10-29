from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from eco_impact.models import ImpactLog
from eco_impact.forms import ImpactLogForm


class ImpactLogModelTests(TestCase):
    """Pengujian logika model dan perhitungan metrik dampak lingkungan"""

    def setUp(self):
        self.user = User.objects.create_user(username='customer1', password='password123')
        UserProfile.objects.create(user=self.user, role='customer')

        self.log = ImpactLog.objects.create(
            user=self.user,
            source='manual',
            food_name='Roti Cokelat',
            quantity=2,
            original_price=Decimal('20000.00'),
            discounted_price=Decimal('10000.00'),
            notes='Penyelamatan mandiri'
        )

    def test_money_saved_calculation(self):
        # Penghematan: (20.000 - 10.000) * 2 = 20.000
        self.assertEqual(self.log.money_saved, Decimal('20000.00'))

    def test_carbon_prevented_calculation(self):
        # Emisi dicegah: 2 porsi * 0.3 kg * 2.5 faktor emisi = 1.5 kg CO2
        self.assertEqual(self.log.carbon_prevented_kg, 1.5)

    def test_string_representation(self):
        self.assertIn('customer1', str(self.log))
        self.assertIn('Roti Cokelat', str(self.log))


class ImpactLogViewsTests(TestCase):
    """Pengujian hak akses peran dan operasi CRUD"""

    def setUp(self):
        # Buat akun Customer
        self.customer = User.objects.create_user(username='customer1', password='password123')
        UserProfile.objects.create(user=self.customer, role='customer')

        # Buat akun Customer lain (untuk uji privasi data)
        self.other_customer = User.objects.create_user(username='customer2', password='password123')
        UserProfile.objects.create(user=self.other_customer, role='customer')

        # Buat akun Merchant (untuk uji larangan akses)
        self.merchant = User.objects.create_user(username='merchant1', password='password123')
        UserProfile.objects.create(user=self.merchant, role='merchant')

        self.client = Client()

    def test_dashboard_requires_login(self):
        # Pengguna belum login harus diarahkan ke login
        response = self.client.get(reverse('eco_impact:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_by_customer(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('eco_impact:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'eco_impact/dashboard.html')

    def test_dashboard_forbidden_for_merchant(self):
        # Role merchant dilarang mengakses modul eco impact customer (403 PermissionDenied)
        self.client.login(username='merchant1', password='password123')
        response = self.client.get(reverse('eco_impact:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_create_manual_log(self):
        self.client.login(username='customer1', password='password123')
        data = {
            'food_name': 'Croissant Almond',
            'quantity': 1,
            'original_price': '25000',
            'discounted_price': '15000',
            'notes': 'Masih renyah'
        }
        response = self.client.post(reverse('eco_impact:create_log'), data)
        self.assertRedirects(response, reverse('eco_impact:dashboard'))
        self.assertEqual(ImpactLog.objects.filter(food_name='Croissant Almond').count(), 1)
        log = ImpactLog.objects.get(food_name='Croissant Almond')
        self.assertEqual(log.source, 'manual')
        self.assertEqual(log.user, self.customer)

    def test_edit_manual_log(self):
        self.client.login(username='customer1', password='password123')
        log = ImpactLog.objects.create(
            user=self.customer, source='manual', food_name='Nasi Bento',
            quantity=1, original_price=Decimal('30000'), discounted_price=Decimal('18000')
        )
        data = {
            'food_name': 'Nasi Bento Spesial',
            'quantity': 2,
            'original_price': '30000',
            'discounted_price': '18000',
            'notes': 'Update porsi'
        }
        response = self.client.post(reverse('eco_impact:edit_log', kwargs={'pk': log.pk}), data)
        self.assertRedirects(response, reverse('eco_impact:dashboard'))
        log.refresh_from_db()
        self.assertEqual(log.food_name, 'Nasi Bento Spesial')
        self.assertEqual(log.quantity, 2)

    def test_edit_order_log_is_blocked(self):
        # Log otomatis dari Order tidak boleh diedit manual
        self.client.login(username='customer1', password='password123')
        log = ImpactLog.objects.create(
            user=self.customer, source='order', food_name='Surprise Bag Roti',
            quantity=1, original_price=Decimal('40000'), discounted_price=Decimal('20000')
        )
        data = {
            'food_name': 'Coba Ubah',
            'quantity': 5,
            'original_price': '50000',
            'discounted_price': '10000'
        }
        response = self.client.post(reverse('eco_impact:edit_log', kwargs={'pk': log.pk}), data)
        self.assertRedirects(response, reverse('eco_impact:dashboard'))
        log.refresh_from_db()
        self.assertEqual(log.food_name, 'Surprise Bag Roti')

    def test_delete_manual_log(self):
        self.client.login(username='customer1', password='password123')
        log = ImpactLog.objects.create(
            user=self.customer, source='manual', food_name='Donat',
            quantity=1, original_price=Decimal('10000'), discounted_price=Decimal('5000')
        )
        response = self.client.get(reverse('eco_impact:delete_log', kwargs={'pk': log.pk}))
        self.assertRedirects(response, reverse('eco_impact:dashboard'))
        self.assertFalse(ImpactLog.objects.filter(pk=log.pk).exists())

    def test_delete_order_log_is_blocked(self):
        # Log otomatis dari Order tidak boleh dihapus
        self.client.login(username='customer1', password='password123')
        log = ImpactLog.objects.create(
            user=self.customer, source='order', food_name='Surprise Bag Martabak',
            quantity=1, original_price=Decimal('35000'), discounted_price=Decimal('18000')
        )
        response = self.client.get(reverse('eco_impact:delete_log', kwargs={'pk': log.pk}))
        self.assertRedirects(response, reverse('eco_impact:dashboard'))
        self.assertTrue(ImpactLog.objects.filter(pk=log.pk).exists())

    def test_user_cannot_access_or_modify_other_user_log(self):
        # Log milik customer lain tidak boleh diakses oleh customer1 (404)
        log = ImpactLog.objects.create(
            user=self.other_customer, source='manual', food_name='Milik Customer 2',
            quantity=1, original_price=Decimal('20000'), discounted_price=Decimal('10000')
        )
        self.client.login(username='customer1', password='password123')
        res_edit = self.client.get(reverse('eco_impact:edit_log', kwargs={'pk': log.pk}))
        self.assertEqual(res_edit.status_code, 404)
        res_delete = self.client.get(reverse('eco_impact:delete_log', kwargs={'pk': log.pk}))
        self.assertEqual(res_delete.status_code, 404)


class ImpactLogAPITests(TestCase):
    """Pengujian endpoint AJAX untuk ringkasan metrik dan penyaringan waktu"""

    def setUp(self):
        self.customer = User.objects.create_user(username='customer1', password='password123')
        UserProfile.objects.create(user=self.customer, role='customer')

        # Log 1: Penghematan 20.000, CO2 = 0.75 kg, quantity = 1 (0.3 kg)
        ImpactLog.objects.create(
            user=self.customer, source='manual', food_name='Item 1',
            quantity=1, original_price=Decimal('30000'), discounted_price=Decimal('10000'),
            notes='Toko Roti A'
        )
        # Log 2: Penghematan 20.000, CO2 = 1.50 kg, quantity = 2 (0.6 kg)
        ImpactLog.objects.create(
            user=self.customer, source='manual', food_name='Item 2',
            quantity=2, original_price=Decimal('25000'), discounted_price=Decimal('15000'),
            notes='Warung B'
        )
        self.client = Client()

    def test_summary_api_totals_and_structure(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('eco_impact:summary_api') + '?period=all')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_money_saved'], 40000.0)
        self.assertEqual(data['total_carbon_kg'], 2.2)  # round(2.25, 1) = 2.2
        self.assertEqual(data['total_bags_count'], 3)
        self.assertEqual(data['total_food_kg'], 0.9)  # 3 * 0.3
        self.assertIn('equivalent_km', data)
        self.assertIn('monthly_trend', data)
        self.assertEqual(len(data['monthly_trend']), 6)
        self.assertIn('level', data)

    def test_logs_api_returns_json_list(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('eco_impact:logs_api') + '?period=all')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('logs', data)
        self.assertEqual(len(data['logs']), 2)
        # Verifikasi field store_name terpetakan dari notes atau default
        self.assertEqual(data['logs'][0]['store_name'], 'Warung B')


class ImpactLogFormTests(TestCase):
    """Pengujian validasi form pencatatan dampak manual"""

    def test_valid_form(self):
        form = ImpactLogForm(data={
            'food_name': 'Salad Buah',
            'quantity': 1,
            'original_price': '25000',
            'discounted_price': '15000',
            'notes': 'Segar'
        })
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_required_fields(self):
        form = ImpactLogForm(data={'food_name': ''})
        self.assertFalse(form.is_valid())
