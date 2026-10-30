import uuid
from datetime import date, time
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.db import IntegrityError, transaction

from accounts.models import UserProfile
from merchant_store.models import MerchantStore
from order.models import Order

from .forms import SurpriseBagForm, SurpriseBagUpdateForm
from .models import BagWishlist, SurpriseBag

PASSWORD = 'pass12345'


def make_user(username, role=None, **extra):
    user = User.objects.create_user(username=username, password=PASSWORD, **extra)
    if role:
        UserProfile.objects.create(user=user, role=role)
    return user


def make_bag(merchant, **kwargs):
    data = {
        'name': 'Paket Hemat', 'description': 'Sisa produksi hari ini', 'category': 'mixed',
        'original_price': Decimal('50000'), 'discounted_price': Decimal('30000'),
        'stock': 5, 'pickup_start': time(18), 'pickup_end': time(20),
    }
    data.update(kwargs)
    return SurpriseBag.objects.create(merchant=merchant, **data)


def form_data(**overrides):
    data = {
        'name': 'Paket Baru', 'description': 'Roti dan pastry', 'category': 'bakery', 'image_url': '',
        'original_price': '30000', 'discounted_price': '18000', 'stock': '4',
        'pickup_start': '19:00', 'pickup_end': '21:00', 'is_active': 'on',
    }
    data.update(overrides)
    return data


class SurpriseBagTestCase(TestCase):
    """Data dasar: dua merchant, satu customer, dan satu bag milik `merchant`."""

    @classmethod
    def setUpTestData(cls):
        # data seed migration 0004 ikut masuk ke database test, dibuang supaya hitungan akurat
        SurpriseBag.objects.all().delete()
        cls.merchant = make_user('merchant', 'merchant')
        cls.other_merchant = make_user('other_merchant', 'merchant')
        cls.customer = make_user('customer', 'customer')
        cls.bag = make_bag(
            cls.merchant, name='Roti Sore', category='bakery',
            original_price=Decimal('40000'), discounted_price=Decimal('24000'),
        )


# ============================================================
# MODEL
# ============================================================

class SurpriseBagModelTests(SurpriseBagTestCase):
    def test_str_and_absolute_url(self):
        self.assertEqual(str(self.bag), 'Roti Sore — merchant')
        self.assertEqual(self.bag.get_absolute_url(), reverse('surprise_bag:detail', args=[self.bag.pk]))

    def test_discount_percent(self):
        self.assertEqual(self.bag.discount_percent, 40)
        self.assertEqual(SurpriseBag(original_price=0, discounted_price=0).discount_percent, 0)

    def test_is_available_needs_active_and_stock(self):
        self.assertTrue(self.bag.is_available)
        self.assertFalse(SurpriseBag(is_active=True, stock=0).is_available)
        self.assertFalse(SurpriseBag(is_active=False, stock=5).is_available)

    def test_emoji_follows_category_with_fallback(self):
        self.assertEqual(self.bag.emoji, '🥐')
        self.assertEqual(SurpriseBag(category='unknown').emoji, '🛍️')

    def test_pickup_time_format(self):
        self.assertEqual(self.bag.pickup_time, '18:00–20:00')

    def test_merchant_name_prefers_store_then_full_name_then_username(self):
        def fresh_name():
            return SurpriseBag.objects.get(pk=self.bag.pk).merchant_name

        self.assertEqual(fresh_name(), 'merchant')
        User.objects.filter(pk=self.merchant.pk).update(first_name='Roti', last_name='Senja')
        self.assertEqual(fresh_name(), 'Roti Senja')
        MerchantStore.objects.create(
            owner=self.merchant, name='Toko Roti Senja', address='Depok', phone='0812000000',
            opening_time=time(8), closing_time=time(21),
        )
        self.assertEqual(fresh_name(), 'Toko Roti Senja')

    def test_clean_rejects_price_not_cheaper(self):
        self.bag.discounted_price = self.bag.original_price
        with self.assertRaises(ValidationError) as ctx:
            self.bag.clean()
        self.assertIn('discounted_price', ctx.exception.message_dict)

    def test_clean_rejects_pickup_end_before_start(self):
        self.bag.pickup_end = time(17)
        with self.assertRaises(ValidationError) as ctx:
            self.bag.clean()
        self.assertIn('pickup_end', ctx.exception.message_dict)

    def test_reduce_stock_success(self):
        self.assertTrue(self.bag.reduce_stock(2))
        self.assertEqual(self.bag.stock, 3)

    def test_reduce_stock_rejects_insufficient_stock(self):
        self.assertFalse(self.bag.reduce_stock(10))
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)

    def test_reduce_stock_rejects_inactive_bag(self):
        SurpriseBag.objects.filter(pk=self.bag.pk).update(is_active=False)
        self.assertFalse(self.bag.reduce_stock(1))

    def test_to_dict(self):
        data = self.bag.to_dict()
        self.assertEqual(data['id'], str(self.bag.pk))
        self.assertEqual(data['category_label'], 'Bakery & Pastry')
        self.assertEqual(data['discounted_price'], 24000.0)
        self.assertEqual(data['pickup_start'], '18:00')
        self.assertTrue(data['is_available'])
        self.assertEqual(data['detail_url'], self.bag.get_absolute_url())

    def test_distance_is_not_set_by_default(self):
        self.assertIsNone(self.bag.distance_km)

    def test_registered_in_admin(self):
        self.assertTrue(admin.site.is_registered(SurpriseBag))


# ============================================================
# FORM
# ============================================================

class SurpriseBagFormTests(SurpriseBagTestCase):
    def test_valid_form(self):
        self.assertTrue(SurpriseBagForm(data=form_data()).is_valid())

    def test_discount_boundaries_30_and_50_percent_are_valid(self):
        for price in ('21000', '15000'):  # tepat 30% dan 50% dari 30.000
            with self.subTest(price=price):
                self.assertTrue(SurpriseBagForm(data=form_data(discounted_price=price)).is_valid())

    def test_discount_outside_30_to_50_percent_is_rejected(self):
        for price in ('27000', '12000'):  # 10% dan 60%
            with self.subTest(price=price):
                form = SurpriseBagForm(data=form_data(discounted_price=price))
                self.assertFalse(form.is_valid())
                self.assertIn('discounted_price', form.errors)

    def test_discounted_price_must_be_cheaper(self):
        form = SurpriseBagForm(data=form_data(discounted_price='30000'))
        self.assertFalse(form.is_valid())
        self.assertIn('discounted_price', form.errors)

    def test_pickup_end_must_be_after_start(self):
        form = SurpriseBagForm(data=form_data(pickup_start='21:00', pickup_end='19:00'))
        self.assertFalse(form.is_valid())
        self.assertIn('pickup_end', form.errors)

    def test_negative_stock_is_rejected(self):
        self.assertFalse(SurpriseBagForm(data=form_data(stock='-1')).is_valid())

    def test_update_form_only_exposes_allowed_fields(self):
        self.assertEqual(
            list(SurpriseBagUpdateForm().fields),
            ['photo', 'discounted_price', 'stock', 'pickup_start', 'pickup_end', 'is_active'],
        )

    def test_update_form_checks_discount_against_saved_original_price(self):
        data = {'discounted_price': '38000', 'stock': '3', 'pickup_start': '18:00', 'pickup_end': '20:00'}
        form = SurpriseBagUpdateForm(data=data, instance=self.bag)  # 38.000 dari 40.000 = diskon 5%
        self.assertFalse(form.is_valid())
        self.assertIn('discounted_price', form.errors)


# ============================================================
# OTORISASI
# ============================================================

class AuthorizationTests(SurpriseBagTestCase):
    def merchant_urls(self):
        return [
            reverse('surprise_bag:my_bags'),
            reverse('surprise_bag:create'),
            reverse('surprise_bag:edit', args=[self.bag.pk]),
        ]

    def test_guest_is_redirected_to_login(self):
        for url in self.merchant_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('next=', response.url)

    def test_customer_gets_403(self):
        self.client.force_login(self.customer)
        for url in self.merchant_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_customer_cannot_create_via_post(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse('surprise_bag:create'), form_data(name='Bag Ilegal'))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SurpriseBag.objects.filter(name='Bag Ilegal').exists())

    def test_user_without_profile_is_not_merchant(self):
        self.client.force_login(make_user('legacy'))
        self.assertEqual(self.client.get(reverse('surprise_bag:my_bags')).status_code, 403)

    def test_other_merchant_gets_404_on_every_owner_action(self):
        self.client.force_login(self.other_merchant)
        pk = self.bag.pk
        self.assertEqual(self.client.get(reverse('surprise_bag:edit', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('surprise_bag:delete', args=[pk])).status_code, 404)
        for name in ('update_stock_api', 'toggle_active_api'):
            with self.subTest(endpoint=name):
                response = self.client.post(reverse(f'surprise_bag:{name}', args=[pk]),
                                            data='{"stock": 1}', content_type='application/json')
                self.assertEqual(response.status_code, 404)
        self.assertTrue(SurpriseBag.objects.filter(pk=pk).exists())


# ============================================================
# READ: DETAIL & INVENTARIS
# ============================================================

class DetailAndInventoryTests(SurpriseBagTestCase):
    def detail(self):
        return self.client.get(reverse('surprise_bag:detail', args=[self.bag.pk]))

    def test_guest_sees_login_to_order(self):
        response = self.detail()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login untuk Memesan')

    def test_customer_sees_order_button(self):
        self.client.force_login(self.customer)
        self.assertContains(self.detail(), reverse('order:create', args=[self.bag.pk]))

    def test_owner_sees_edit_link(self):
        self.client.force_login(self.merchant)
        response = self.detail()
        self.assertTrue(response.context['is_owner'])
        self.assertContains(response, reverse('surprise_bag:edit', args=[self.bag.pk]))

    def test_inactive_bag_only_visible_to_owner(self):
        SurpriseBag.objects.filter(pk=self.bag.pk).update(is_active=False)
        self.assertEqual(self.detail().status_code, 404)
        self.client.force_login(self.customer)
        self.assertEqual(self.detail().status_code, 404)
        self.client.force_login(self.merchant)
        self.assertEqual(self.detail().status_code, 200)

    def test_unknown_bag_returns_404(self):
        self.assertEqual(self.client.get(reverse('surprise_bag:detail', args=[uuid.uuid4()])).status_code, 404)

    def test_my_bags_only_lists_own_bags(self):
        make_bag(self.other_merchant, name='Bag Orang Lain')
        self.client.force_login(self.merchant)
        response = self.client.get(reverse('surprise_bag:my_bags'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([bag.name for bag in response.context['bags']], ['Roti Sore'])


# ============================================================
# CREATE / UPDATE / DELETE
# ============================================================

class CrudTests(SurpriseBagTestCase):
    def setUp(self):
        self.client.force_login(self.merchant)

    def test_create_form_renders(self):
        response = self.client.get(reverse('surprise_bag:create'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SurpriseBagForm)

    def test_create_sets_owner_from_session(self):
        response = self.client.post(reverse('surprise_bag:create'),
                                    form_data(merchant=self.other_merchant.pk))
        self.assertRedirects(response, reverse('surprise_bag:my_bags'))
        bag = SurpriseBag.objects.get(name='Paket Baru')
        self.assertEqual(bag.merchant, self.merchant)

    def test_create_invalid_rerenders_form_with_errors(self):
        response = self.client.post(reverse('surprise_bag:create'), form_data(discounted_price='29000'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(SurpriseBag.objects.filter(name='Paket Baru').exists())

    def test_edit_form_renders(self):
        response = self.client.get(reverse('surprise_bag:edit', args=[self.bag.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SurpriseBagUpdateForm)

    def test_edit_updates_only_allowed_fields(self):
        response = self.client.post(reverse('surprise_bag:edit', args=[self.bag.pk]), {
            'name': 'Nama Diganti', 'discounted_price': '20000', 'stock': '9',
            'pickup_start': '17:00', 'pickup_end': '19:00', 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('surprise_bag:my_bags'))
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.discounted_price, Decimal('20000'))
        self.assertEqual(self.bag.stock, 9)
        self.assertEqual(self.bag.name, 'Roti Sore')  # nama tidak ada di form update

    def test_edit_invalid_keeps_old_data(self):
        response = self.client.post(reverse('surprise_bag:edit', args=[self.bag.pk]), {
            'discounted_price': '39000', 'stock': '9', 'pickup_start': '17:00', 'pickup_end': '19:00',
        })
        self.assertEqual(response.status_code, 200)
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.discounted_price, Decimal('24000'))

    def test_delete_requires_post(self):
        response = self.client.get(reverse('surprise_bag:delete', args=[self.bag.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(SurpriseBag.objects.filter(pk=self.bag.pk).exists())

    def test_delete_removes_bag(self):
        response = self.client.post(reverse('surprise_bag:delete', args=[self.bag.pk]))
        self.assertRedirects(response, reverse('surprise_bag:my_bags'))
        self.assertFalse(SurpriseBag.objects.filter(pk=self.bag.pk).exists())

    def test_delete_bag_with_orders_deactivates_instead(self):
        Order.objects.create(
            customer=self.customer, surprise_bag=self.bag, food_name=self.bag.name, quantity=1,
            original_price=self.bag.original_price, discounted_price=self.bag.discounted_price,
            pickup_date=date.today(), pickup_start=self.bag.pickup_start, pickup_end=self.bag.pickup_end,
            reservation_key=uuid.uuid4(),
        )
        response = self.client.post(reverse('surprise_bag:delete', args=[self.bag.pk]))
        self.assertRedirects(response, reverse('surprise_bag:my_bags'))
        self.bag.refresh_from_db()
        self.assertFalse(self.bag.is_active)


# ============================================================
# AJAX: STOK & STATUS AKTIF
# ============================================================

class StockAndToggleApiTests(SurpriseBagTestCase):
    def setUp(self):
        self.client.force_login(self.merchant)

    def post(self, name, body):
        return self.client.post(reverse(f'surprise_bag:{name}', args=[self.bag.pk]),
                                data=body, content_type='application/json')

    def test_stock_delta(self):
        response = self.post('update_stock_api', '{"delta": -2}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['stock'], 3)

    def test_stock_absolute_value(self):
        self.assertEqual(self.post('update_stock_api', '{"stock": 12}').json()['stock'], 12)

    def test_stock_rejects_negative_and_invalid_payloads(self):
        for body in ('{"stock": -1}', '{"delta": -99}', 'bukan json', '{}', '{"stock": "abc"}'):
            with self.subTest(body=body):
                response = self.post('update_stock_api', body)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.json())
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)

    def test_stock_api_requires_post(self):
        response = self.client.get(reverse('surprise_bag:update_stock_api', args=[self.bag.pk]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_sets_explicit_value(self):
        self.assertFalse(self.post('toggle_active_api', '{"is_active": false}').json()['is_active'])
        self.assertTrue(self.post('toggle_active_api', '{"is_active": true}').json()['is_active'])

    def test_toggle_without_body_flips_status(self):
        self.assertFalse(self.post('toggle_active_api', '').json()['is_active'])

    def test_toggle_rejects_invalid_json(self):
        self.assertEqual(self.post('toggle_active_api', '{rusak').status_code, 400)

    def test_customer_cannot_use_api(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.post('update_stock_api', '{"stock": 1}').status_code, 403)


# ============================================================
# KATALOG: FILTER, URUTAN, AJAX
# ============================================================

class CatalogFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SurpriseBag.objects.all().delete()
        cls.merchant = make_user('merchant', 'merchant')
        make_bag(cls.merchant, name='Croissant Butter', category='bakery',
                 original_price=Decimal('40000'), discounted_price=Decimal('24000'))  # diskon 40%
        make_bag(cls.merchant, name='Nasi Ayam', category='meal', stock=0,
                 original_price=Decimal('30000'), discounted_price=Decimal('18000'))
        make_bag(cls.merchant, name='Brownies Fudge', category='dessert', description='Rasa cokelat pekat',
                 original_price=Decimal('50000'), discounted_price=Decimal('25000'))  # diskon 50%
        make_bag(cls.merchant, name='Es Kopi', category='beverage', is_active=False)

    def names(self, **params):
        response = self.client.get(reverse('surprise_bag:catalog'), params)
        self.assertEqual(response.status_code, 200)
        return [bag.name for bag in response.context['bags']]

    def test_default_hides_sold_out_and_inactive(self):
        self.assertCountEqual(self.names(), ['Croissant Butter', 'Brownies Fudge'])

    def test_stock_all_includes_sold_out_but_never_inactive(self):
        self.assertCountEqual(self.names(stock='all'), ['Croissant Butter', 'Nasi Ayam', 'Brownies Fudge'])

    def test_search_matches_name_and_description(self):
        self.assertEqual(self.names(q='croissant'), ['Croissant Butter'])
        self.assertEqual(self.names(q='cokelat'), ['Brownies Fudge'])

    def test_category_filter_and_unknown_category_is_ignored(self):
        self.assertEqual(self.names(category='dessert'), ['Brownies Fudge'])
        self.assertEqual(len(self.names(category='tidak-ada')), 2)

    def test_price_range_and_invalid_price_is_ignored(self):
        self.assertEqual(self.names(min_price='24500'), ['Brownies Fudge'])
        self.assertEqual(self.names(max_price='24000'), ['Croissant Butter'])
        self.assertEqual(len(self.names(min_price='abc', max_price='NaN')), 2)

    def test_sorting(self):
        self.assertEqual(self.names(sort='price_asc'), ['Croissant Butter', 'Brownies Fudge'])
        self.assertEqual(self.names(sort='price_desc'), ['Brownies Fudge', 'Croissant Butter'])
        self.assertEqual(self.names(sort='discount'), ['Brownies Fudge', 'Croissant Butter'])

    def test_unknown_sort_falls_back_to_newest(self):
        response = self.client.get(reverse('surprise_bag:catalog'), {'sort': 'hack'})
        self.assertEqual(response.context['filters']['sort'], 'newest')

    def test_ajax_request_returns_results_fragment_only(self):
        response = self.client.get(reverse('surprise_bag:catalog'), headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertTemplateUsed(response, 'surprise_bag/components/catalog_results.html')
        self.assertTemplateNotUsed(response, 'surprise_bag/catalog.html')
        self.assertNotContains(response, '<html')

    def test_merchant_sees_manage_link(self):
        self.client.force_login(self.merchant)
        response = self.client.get(reverse('surprise_bag:catalog'))
        self.assertTrue(response.context['is_merchant'])
        self.assertContains(response, reverse('surprise_bag:my_bags'))

    def test_catalog_api_returns_json_with_filters(self):
        data = self.client.get(reverse('surprise_bag:catalog_api'), {'available': '1'}).json()
        self.assertEqual(data['count'], 2)
        self.assertNotIn('Nasi Ayam', [bag['name'] for bag in data['bags']])
        all_data = self.client.get(reverse('surprise_bag:catalog_api')).json()
        self.assertEqual(all_data['count'], 3)

    def test_bag_api_hides_inactive_bag_from_public(self):
        inactive = SurpriseBag.objects.get(name='Es Kopi')
        self.assertEqual(self.client.get(reverse('surprise_bag:bag_api', args=[inactive.pk])).status_code, 404)
        self.client.force_login(self.merchant)
        response = self.client.get(reverse('surprise_bag:bag_api', args=[inactive.pk]))
        self.assertEqual(response.json()['name'], 'Es Kopi')


class CatalogPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SurpriseBag.objects.all().delete()
        merchant = make_user('merchant', 'merchant')
        bags = [
            SurpriseBag(merchant=merchant, name=f'Bag {i}', description='-', category='dessert' if i < 15 else 'mixed',
                        original_price=Decimal('50000'), discounted_price=Decimal('30000'), stock=5,
                        pickup_start=time(18), pickup_end=time(20))
            for i in range(100)
        ]
        SurpriseBag.objects.bulk_create(bags)

    def get(self, **params):
        return self.client.get(reverse('surprise_bag:catalog'), params)

    def test_twelve_bags_per_page(self):
        response = self.get(page=9)
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 9)
        self.assertEqual(len(response.context['bags']), 4)  # 100 - 8*12

    def test_invalid_or_out_of_range_page_falls_back(self):
        for requested, expected in (('abc', 1), ('99', 9)):
            with self.subTest(page=requested):
                self.assertEqual(self.get(page=requested).context['page_obj'].number, expected)

    def test_many_pages_use_ellipsis(self):
        response = self.get(page=5)
        ellipsis = response.context['page_obj'].paginator.ELLIPSIS
        self.assertEqual(response.context['page_numbers'], [1, ellipsis, 3, 4, 5, 6, 7, ellipsis, 9])

    def test_few_pages_show_every_number(self):
        self.assertEqual(self.get(category='dessert').context['page_numbers'], [1, 2])

    def test_page_links_keep_filters(self):
        self.assertContains(self.get(category='dessert'), '?category=dessert&amp;page=2')


class CatalogNearestSortTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SurpriseBag.objects.all().delete()
        near = make_user('merchant_near', 'merchant')
        far = make_user('merchant_far', 'merchant')
        no_store = make_user('merchant_nostore', 'merchant')
        store = {'address': 'Depok', 'phone': '0812000000', 'opening_time': time(8), 'closing_time': time(21)}
        MerchantStore.objects.create(owner=near, name='Toko Dekat', latitude=-6.3600, longitude=106.8270, **store)
        MerchantStore.objects.create(owner=far, name='Toko Jauh', latitude=-6.2000, longitude=106.8166, **store)
        # urutan pembuatan: jauh -> tanpa toko -> dekat (yang terakhir = paling baru)
        make_bag(far, name='Bag Jauh')
        make_bag(no_store, name='Bag Tanpa Toko')
        make_bag(near, name='Bag Dekat')
        cls.location = {'lat': '-6.3650', 'lng': '106.8240'}  # sekitar Fasilkom UI

    def get(self, **params):
        response = self.client.get(reverse('surprise_bag:catalog'), params)
        return [bag.name for bag in response.context['bags']], response

    def test_nearest_sorts_by_distance_and_puts_unknown_last(self):
        names, _ = self.get(sort='nearest', **self.location)
        self.assertEqual(names, ['Bag Dekat', 'Bag Jauh', 'Bag Tanpa Toko'])

    def test_nearest_without_location_falls_back_to_newest(self):
        names, _ = self.get(sort='nearest')
        self.assertEqual(names, ['Bag Dekat', 'Bag Tanpa Toko', 'Bag Jauh'])

    def test_distance_shown_with_store_name(self):
        _, response = self.get(sort='nearest', **self.location)
        nearest = response.context['bags'][0]
        self.assertLess(nearest.distance_km, 1)
        self.assertContains(response, 'Toko Dekat')
        self.assertContains(response, 'di sekitarmu')

    def test_invalid_coordinates_are_ignored(self):
        for lat, lng in (('999', '106.8'), ('abc', 'def'), ('nan', '106.8')):
            with self.subTest(lat=lat, lng=lng):
                _, response = self.get(sort='nearest', lat=lat, lng=lng)
                self.assertEqual(response.context['filters']['lat'], '')

# ============================================================
# WISHLIST
# ============================================================

class BagWishlistTests(SurpriseBagTestCase):
    def toggle_url(self, bag=None):
        return reverse('surprise_bag:wishlist_toggle', args=[(bag or self.bag).pk])

    def toggle(self, bag=None):
        return self.client.post(self.toggle_url(bag))

    def test_str(self):
        item = BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        self.assertEqual(str(item), 'customer ♥ Roti Sore')

    def test_customer_can_add_and_remove(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.toggle().json(), {'wishlisted': True})
        self.assertTrue(BagWishlist.objects.filter(customer=self.customer, bag=self.bag).exists())
        self.assertEqual(self.toggle().json(), {'wishlisted': False})
        self.assertFalse(BagWishlist.objects.exists())

    def test_guest_gets_401_and_merchant_gets_403(self):
        self.assertEqual(self.toggle().status_code, 401)
        self.client.force_login(self.merchant)
        self.assertEqual(self.toggle().status_code, 403)
        self.assertFalse(BagWishlist.objects.exists())

    def test_toggle_requires_post(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.toggle_url()).status_code, 405)

    def test_unknown_bag_returns_404(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse('surprise_bag:wishlist_toggle', args=[uuid.uuid4()])).status_code, 404)

    def test_inactive_bag_can_be_removed_but_not_added(self):
        self.client.force_login(self.customer)
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        SurpriseBag.objects.filter(pk=self.bag.pk).update(is_active=False)
        self.assertEqual(self.toggle().json(), {'wishlisted': False})
        self.assertEqual(self.toggle().status_code, 404)
        self.assertFalse(BagWishlist.objects.exists())

    def test_same_bag_cannot_be_saved_twice(self):
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BagWishlist.objects.create(customer=self.customer, bag=self.bag)

    def test_bag_ids_for(self):
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        self.assertEqual(BagWishlist.bag_ids_for(self.customer), {self.bag.pk})
        self.assertEqual(BagWishlist.bag_ids_for(self.other_merchant), set())
        self.assertEqual(BagWishlist.bag_ids_for(AnonymousUser()), set())

    def test_catalog_heart_only_for_customer_and_shows_saved_state(self):
        catalog = reverse('surprise_bag:catalog')
        self.assertNotContains(self.client.get(catalog), self.toggle_url())
        self.client.force_login(self.merchant)
        self.assertNotContains(self.client.get(catalog), self.toggle_url())

        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        self.client.force_login(self.customer)
        response = self.client.get(catalog)
        self.assertContains(response, self.toggle_url())
        self.assertContains(response, 'data-wishlisted="true"')

    def test_detail_shows_wishlist_state(self):
        detail = reverse('surprise_bag:detail', args=[self.bag.pk])
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(detail), '♡ Simpan')
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        response = self.client.get(detail)
        self.assertTrue(response.context['is_wishlisted'])
        self.assertContains(response, '♥ Tersimpan')

    def test_wishlist_page_lists_only_own_active_bags(self):
        inactive = make_bag(self.merchant, name='Bag Nonaktif', is_active=False)
        other_customer = make_user('customer2', 'customer')
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        BagWishlist.objects.create(customer=self.customer, bag=inactive)
        BagWishlist.objects.create(customer=other_customer, bag=self.bag)

        self.client.force_login(self.customer)
        response = self.client.get(reverse('merchant_store:wishlist'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bags'], [self.bag])
        self.assertContains(response, 'id="mw-bag-count">1</span>')
        self.assertContains(response, 'data-remove-on-unwish="true"')

    def test_landing_page_has_heart_and_csrf_for_customer(self):
        BagWishlist.objects.create(customer=self.customer, bag=self.bag)
        self.client.force_login(self.customer)
        response = self.client.get(reverse('main:home'))
        self.assertContains(response, self.toggle_url())
        self.assertContains(response, 'data-csrf=')  # wishlist.js butuh token CSRF dari atribut ini
        self.assertContains(response, 'css/landing.css')


# ============================================================
# DATA AWAL (SEED)
# ============================================================

class SeedDataTests(TestCase):
    def test_seed_migration_provides_at_least_50_bags(self):
        # migration 0004 otomatis jalan juga di database test
        self.assertGreaterEqual(SurpriseBag.objects.count(), 50)

    def test_seed_merchants_have_merchant_role(self):
        merchants = User.objects.filter(username__startswith='dummy_merchant_')
        self.assertTrue(merchants.exists())
        self.assertFalse(merchants.exclude(profile__role='merchant').exists())
