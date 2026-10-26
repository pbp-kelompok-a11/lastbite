from datetime import datetime, time, timezone as dt_timezone
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import UserProfile

from . import services
from .forms import MerchantStoreForm
from .models import MerchantStore, StoreWishlist
from .services import GeocodingError

User = get_user_model()

UI = (-6.3628, 106.8272)  # pusat pencarian pada tes


def make_user(username, role):
    user = User.objects.create_user(username=username, password='LastBite-Test-937!')
    UserProfile.objects.create(user=user, role=role)
    return user


def make_store(owner, **overrides):
    data = {
        'name': 'Toko Uji', 'address': 'Jl. Margonda Raya No. 1, Depok', 'phone': '081234567890',
        'opening_time': time(8, 0), 'closing_time': time(21, 0),
        'latitude': UI[0], 'longitude': UI[1],
    }
    data.update(overrides)
    return MerchantStore.objects.create(owner=owner, **data)


def form_data(**changes):
    data = {
        'name': 'Bakers Corner', 'description': 'Roti enak', 'address': 'Jl. Margonda Raya No. 100, Depok',
        'phone': '081234567890', 'business_email': 'toko@example.com',
        'opening_time': '08:00', 'closing_time': '21:00',
    }
    data.update(changes)
    return data


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])  # agar tes cepat
class BaseCase(TestCase):
    def setUp(self):
        cache.clear()
        # Pengaman: tes tidak boleh memanggil Nominatim sungguhan
        patcher = mock.patch.object(services, '_request_nominatim', side_effect=AssertionError('Tes memanggil jaringan!'))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.merchant = make_user('merchant1', 'merchant')
        self.merchant2 = make_user('merchant2', 'merchant')
        self.customer = make_user('customer1', 'customer')


# Services
class ServicesTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_haversine_known_distance(self):
        # Jakarta (Monas) -> Depok (UI) sekitar 22-25 km
        distance = services.haversine_km(-6.1754, 106.8272, -6.3628, 106.8272)
        self.assertAlmostEqual(distance, 20.8, delta=0.5)
        self.assertEqual(services.haversine_km(1, 1, 1, 1), 0)

    def test_bounding_box_contains_circle(self):
        min_lat, max_lat, min_lng, max_lng = services.bounding_box(*UI, 3)
        self.assertLess(min_lat, UI[0]); self.assertGreater(max_lat, UI[0])
        self.assertLess(min_lng, UI[1]); self.assertGreater(max_lng, UI[1])

    def test_geocode_returns_result_and_caches(self):
        found = {'lat': -6.36, 'lng': 106.82, 'display_name': 'Depok'}
        with mock.patch.object(services, '_request_nominatim', return_value=found) as req:
            self.assertEqual(services.geocode_address('Jl. Margonda, Depok'), found)
            self.assertEqual(services.geocode_address('jl.  margonda,  depok'), found)
        self.assertEqual(req.call_count, 1)

    def test_geocode_falls_back_to_shorter_query(self):
        found = {'lat': -6.36, 'lng': 106.82, 'display_name': 'Pondok Cina'}
        with mock.patch.object(services, '_request_nominatim', side_effect=[None, found]) as req, \
                mock.patch.object(services.time, 'sleep'):
            result = services.geocode_address('Jl. Margonda No. 12, Pondok Cina, Depok')
        self.assertEqual(result, found)
        self.assertEqual(req.call_args_list[1].args[0], 'Pondok Cina, Depok')

    def test_geocode_not_found_and_error(self):
        with mock.patch.object(services, '_request_nominatim', return_value=None), \
                mock.patch.object(services.time, 'sleep'):
            self.assertIsNone(services.geocode_address('zzz qqq, yyy'))
        cache.clear()
        with mock.patch.object(services, '_request_nominatim', side_effect=GeocodingError('down')), \
                mock.patch.object(services.time, 'sleep'):
            with self.assertRaises(GeocodingError):
                services.geocode_address('Jl. Apa Saja No. 1, Depok')
        self.assertIsNone(services.geocode_address('  '))



# Model & form
class ModelAndFormTests(BaseCase):
    def _at(self, hour, minute=0):
        return mock.patch(
            'django.utils.timezone.now',
            return_value=datetime(2026, 10, 24, hour, minute, tzinfo=dt_timezone.utc),
        )

    def test_is_open_now_same_day(self):
        store = make_store(self.merchant)  # 08:00-21:00 WIB
        with self._at(3):    # 10:00 WIB
            self.assertTrue(store.is_open_now())
        with self._at(15):   # 22:00 WIB
            self.assertFalse(store.is_open_now())

    def test_is_open_now_overnight(self):
        store = make_store(self.merchant, opening_time=time(18, 0), closing_time=time(2, 0))
        with self._at(14):   # 21:00 WIB
            self.assertTrue(store.is_open_now())
        with self._at(5):    # 12:00 WIB
            self.assertFalse(store.is_open_now())

    def test_one_store_per_merchant(self):
        make_store(self.merchant)
        with self.assertRaises(Exception):
            make_store(self.merchant, name='Kedua')

    def test_form_valid_and_invalid(self):
        self.assertTrue(MerchantStoreForm(form_data()).is_valid())
        for bad in ({'phone': 'abc'}, {'name': 'ab'}, {'address': 'pendek'},
                    {'closing_time': '08:00'}, {'business_email': 'bukan-email'}):
            with self.subTest(bad=bad):
                self.assertFalse(MerchantStoreForm(form_data(**bad)).is_valid())



# Hak akses & CRUD merchant
class MerchantCrudTests(BaseCase):
    found = {'lat': -6.37, 'lng': 106.83, 'display_name': 'Depok'}

    def test_manage_pages_require_merchant_role(self):
        urls = [reverse(f'merchant_store:{n}') for n in ('my_store', 'create', 'edit')]
        for url in urls:
            with self.subTest(url=url, who='guest'):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)
        self.client.force_login(self.customer)
        for url in urls:
            with self.subTest(url=url, who='customer'):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.get(urls[0]).status_code, 200)
        self.assertEqual(self.client.get(urls[1]).status_code, 200)

    def test_create_store_geocodes_address(self):
        self.client.force_login(self.merchant)
        with mock.patch('merchant_store.views.geocode_address', return_value=self.found) as geo:
            response = self.client.post(reverse('merchant_store:create'), form_data())
        self.assertRedirects(response, reverse('merchant_store:my_store'))
        store = MerchantStore.objects.get(owner=self.merchant)
        self.assertEqual((store.latitude, store.longitude), (-6.37, 106.83))
        self.assertTrue(store.is_active)
        geo.assert_called_once()

    def test_create_survives_geocoding_failure(self):
        self.client.force_login(self.merchant)
        with mock.patch('merchant_store.views.geocode_address', side_effect=GeocodingError('down')):
            response = self.client.post(reverse('merchant_store:create'), form_data(), follow=True)
        store = MerchantStore.objects.get(owner=self.merchant)
        self.assertIsNone(store.latitude)
        self.assertIn('warning', [m.level_tag for m in response.context['messages']])

    def test_create_address_not_found_saves_without_coordinates(self):
        self.client.force_login(self.merchant)
        with mock.patch('merchant_store.views.geocode_address', return_value=None):
            self.client.post(reverse('merchant_store:create'), form_data())
        self.assertFalse(MerchantStore.objects.get(owner=self.merchant).has_coordinates)

    def test_invalid_create_saves_nothing(self):
        self.client.force_login(self.merchant)
        with mock.patch('merchant_store.views.geocode_address') as geo:
            response = self.client.post(reverse('merchant_store:create'), form_data(phone='x'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MerchantStore.objects.exists())
        geo.assert_not_called()

    def test_second_create_redirects(self):
        make_store(self.merchant)
        self.client.force_login(self.merchant)
        response = self.client.post(reverse('merchant_store:create'), form_data())
        self.assertRedirects(response, reverse('merchant_store:my_store'))
        self.assertEqual(MerchantStore.objects.filter(owner=self.merchant).count(), 1)

    def test_edit_regeocodes_only_when_address_changes(self):
        store = make_store(self.merchant, address='Jl. Margonda Raya No. 100, Depok')
        self.client.force_login(self.merchant)
        url = reverse('merchant_store:edit')
        with mock.patch('merchant_store.views.geocode_address', return_value=self.found) as geo:
            self.client.post(url, form_data(name='Nama Baru', address=store.address))
            geo.assert_not_called()
            self.client.post(url, form_data(address='Jl. Kukusan Teknik No. 5, Depok'))
            geo.assert_called_once()
        store.refresh_from_db()
        self.assertEqual(store.address, 'Jl. Kukusan Teknik No. 5, Depok')
        self.assertEqual(store.latitude, -6.37)

    def test_merchant_cannot_touch_other_store(self):
        other = make_store(self.merchant2, name='Milik Orang Lain')
        self.client.force_login(self.merchant)
        make_store(self.merchant, name='Milik Saya')
        with mock.patch('merchant_store.views.geocode_address', return_value=self.found):
            self.client.post(reverse('merchant_store:edit'), form_data(name='Dibajak'))
        self.client.post(reverse('merchant_store:toggle_active'))
        self.client.post(reverse('merchant_store:delete'))
        other.refresh_from_db()
        self.assertEqual(other.name, 'Milik Orang Lain')
        self.assertTrue(other.is_active)
        self.assertFalse(MerchantStore.objects.filter(owner=self.merchant).exists())

    def test_toggle_and_delete_require_post(self):
        make_store(self.merchant)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.get(reverse('merchant_store:toggle_active')).status_code, 405)
        self.assertEqual(self.client.get(reverse('merchant_store:delete')).status_code, 405)

    def test_toggle_active_flips_state(self):
        store = make_store(self.merchant)
        self.client.force_login(self.merchant)
        self.client.post(reverse('merchant_store:toggle_active'))
        store.refresh_from_db(); self.assertFalse(store.is_active)
        self.client.post(reverse('merchant_store:toggle_active'))
        store.refresh_from_db(); self.assertTrue(store.is_active)

    def test_delete_removes_store_and_wishlist(self):
        store = make_store(self.merchant)
        StoreWishlist.objects.create(customer=self.customer, store=store)
        self.client.force_login(self.merchant)
        self.client.post(reverse('merchant_store:delete'))
        self.assertFalse(MerchantStore.objects.exists())
        self.assertFalse(StoreWishlist.objects.exists())

    def test_edit_without_store_redirects_to_create(self):
        self.client.force_login(self.merchant)
        self.assertRedirects(self.client.get(reverse('merchant_store:edit')), reverse('merchant_store:create'))


# Read publik
class PublicReadTests(BaseCase):
    def test_directory_and_detail_open_to_guest(self):
        store = make_store(self.merchant)
        self.assertEqual(self.client.get(reverse('merchant_store:list')).status_code, 200)
        response = self.client.get(reverse('merchant_store:detail', args=[store.id]))
        self.assertContains(response, 'Toko Uji')
        self.assertContains(response, 'Belum ada rating')

    def test_inactive_store_hidden_except_owner(self):
        store = make_store(self.merchant, is_active=False)
        url = reverse('merchant_store:detail', args=[store.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_detail_map_coordinates_use_dot_not_locale_comma(self):
        store = make_store(self.merchant, latitude=-6.3628, longitude=106.8272)
        html = self.client.get(reverse('merchant_store:detail', args=[store.id])).content.decode()
        self.assertIn('data-lat="-6.3628"', html)
        self.assertIn('data-lng="106.8272"', html)

    def test_store_name_is_escaped(self):
        store = make_store(self.merchant, name='<script>alert(1)</script>')
        html = self.client.get(reverse('merchant_store:detail', args=[store.id])).content.decode()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)

    def test_list_page_coordinates_use_dot(self):
        html = self.client.get(reverse('merchant_store:list')).content.decode()
        self.assertIn('data-default-lat="-6.3628"', html)


# API pencarian + radius
class SearchApiTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('merchant_store:api_search')
        # Jarak dari UI (-6.3628, 106.8272): ~0.5 km, ~2.2 km, ~4.4 km, ~11 km
        self.near = make_store(self.merchant, name='Dekat', latitude=-6.3673, longitude=106.8272)
        self.mid = make_store(make_user('m3', 'merchant'), name='Menengah', latitude=-6.3828, longitude=106.8272)
        self.far = make_store(make_user('m4', 'merchant'), name='Agak Jauh', latitude=-6.4024, longitude=106.8272)
        self.very_far = make_store(make_user('m5', 'merchant'), name='Sangat Jauh', latitude=-6.4628, longitude=106.8272)

    def names(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200, response.content)
        return [s['name'] for s in response.json()['stores']]

    def test_all_stores_for_guest(self):
        data = self.client.get(self.url).json()
        self.assertEqual(data['count'], 4)
        self.assertFalse(data['can_wishlist'])
        self.assertNotIn('wishlist_url', data['stores'][0])

    def test_radius_filters(self):
        base = {'lat': UI[0], 'lng': UI[1]}
        self.assertEqual(self.names(**base, radius=1), ['Dekat'])
        self.assertEqual(self.names(**base, radius=3), ['Dekat', 'Menengah'])
        self.assertEqual(self.names(**base, radius=5), ['Dekat', 'Menengah', 'Agak Jauh'])

    def test_sorted_by_distance_without_radius_and_reports_distance(self):
        data = self.client.get(self.url, {'lat': UI[0], 'lng': UI[1]}).json()
        self.assertEqual([s['name'] for s in data['stores']], ['Dekat', 'Menengah', 'Agak Jauh', 'Sangat Jauh'])
        self.assertAlmostEqual(data['stores'][0]['distance_km'], 0.5, delta=0.1)

    def test_text_query_and_inactive_excluded(self):
        self.assertEqual(self.names(q='dekat'), ['Dekat'])
        self.mid.is_active = False
        self.mid.save()
        self.assertNotIn('Menengah', self.names())

    def test_store_without_coordinates(self):
        make_store(make_user('m6', 'merchant'), name='Tanpa Peta', latitude=None, longitude=None)
        self.assertIn('Tanpa Peta', self.names())
        self.assertNotIn('Tanpa Peta', self.names(lat=UI[0], lng=UI[1], radius=5))
        self.assertEqual(self.names(lat=UI[0], lng=UI[1])[-1], 'Tanpa Peta')

    def test_bad_parameters(self):
        for params in ({'lat': 'abc', 'lng': '1'}, {'lat': '95', 'lng': '1'}, {'lat': 'nan', 'lng': '1'},
                        {'lat': '1'}, {'radius': '3'}, {'lat': '1', 'lng': '1', 'radius': '-2'},
                        {'lat': '1', 'lng': '1', 'radius': '999'}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.url, params).status_code, 400)

    def test_customer_sees_wishlist_state(self):
        StoreWishlist.objects.create(customer=self.customer, store=self.near)
        self.client.force_login(self.customer)
        data = self.client.get(self.url).json()
        self.assertTrue(data['can_wishlist'])
        by_name = {s['name']: s for s in data['stores']}
        self.assertTrue(by_name['Dekat']['wishlisted'])
        self.assertFalse(by_name['Menengah']['wishlisted'])
        self.assertIn('wishlist_url', by_name['Dekat'])

    def test_post_not_allowed(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)


# API geocode
class GeocodeApiTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('merchant_store:api_geocode')

    def test_validation_and_statuses(self):
        self.assertEqual(self.client.get(self.url, {'q': 'ab'}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {'q': 'x' * 300}).status_code, 400)
        with mock.patch('merchant_store.views.geocode_address', return_value=None):
            self.assertEqual(self.client.get(self.url, {'q': 'tidak ada'}).status_code, 404)
        with mock.patch('merchant_store.views.geocode_address', side_effect=GeocodingError('x')):
            self.assertEqual(self.client.get(self.url, {'q': 'margonda'}).status_code, 502)
        found = {'lat': -6.36, 'lng': 106.82, 'display_name': 'Depok'}
        with mock.patch('merchant_store.views.geocode_address', return_value=found):
            response = self.client.get(self.url, {'q': 'margonda'})
        self.assertEqual(response.json(), found)

    def test_throttle(self):
        found = {'lat': 1.0, 'lng': 2.0, 'display_name': 'x'}
        with mock.patch('merchant_store.views.geocode_address', return_value=found):
            codes = [self.client.get(self.url, {'q': 'margonda'}).status_code for _ in range(22)]
        self.assertEqual(codes.count(200), 20)
        self.assertEqual(codes[-1], 429)


# Wishlist
class WishlistTests(BaseCase):
    def setUp(self):
        super().setUp()
        self.store = make_store(self.merchant)
        self.toggle_url = reverse('merchant_store:wishlist_toggle', args=[self.store.id])

    def test_guest_gets_401_and_merchant_gets_403(self):
        self.assertEqual(self.client.post(self.toggle_url).status_code, 401)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.post(self.toggle_url).status_code, 403)
        self.assertFalse(StoreWishlist.objects.exists())

    def test_customer_toggle_on_and_off(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.toggle_url).json(), {'wishlisted': True})
        self.assertEqual(StoreWishlist.objects.count(), 1)
        self.assertEqual(self.client.post(self.toggle_url).json(), {'wishlisted': False})
        self.assertEqual(StoreWishlist.objects.count(), 0)

    def test_toggle_requires_post(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.toggle_url).status_code, 405)

    def test_cannot_add_inactive_but_can_remove(self):
        self.store.is_active = False
        self.store.save()
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.toggle_url).status_code, 404)
        StoreWishlist.objects.create(customer=self.customer, store=self.store)
        self.assertEqual(self.client.post(self.toggle_url).json(), {'wishlisted': False})

    def test_unknown_store_404(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse('merchant_store:wishlist_toggle', args=[9999])).status_code, 404)

    def test_wishlist_page_is_private_to_customer(self):
        StoreWishlist.objects.create(customer=self.customer, store=self.store)
        url = reverse('merchant_store:wishlist')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(make_user('customer2', 'customer'))
        self.assertNotContains(self.client.get(url), 'Toko Uji')
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(url), 'Toko Uji')


class SeedCommandTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command('seed_stores', stdout=StringIO())
        count = MerchantStore.objects.count()
        self.assertEqual(count, 10)
        call_command('seed_stores', stdout=StringIO())
        self.assertEqual(MerchantStore.objects.count(), count)
