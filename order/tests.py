import uuid
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import UserProfile
from eco_impact.models import ImpactLog
from surprise_bag.models import SurpriseBag

from .models import Order
from .services import reserve_bag, transition_order


class OrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def user(name, role):
            actor = get_user_model().objects.create_user(username=name)
            if role:
                UserProfile.objects.create(user=actor, role=role)
            return actor
        cls.customer = user('customer', 'customer')
        cls.other_customer = user('other_customer', 'customer')
        cls.merchant = user('merchant', 'merchant')
        cls.other_merchant = user('other_merchant', 'merchant')
        cls.legacy = user('legacy', None)
        cls.bag = SurpriseBag.objects.create(
            merchant=cls.merchant, name='Paket Roti', description='Roti hari ini',
            category='bakery', original_price=50000, discounted_price=30000,
            stock=5, pickup_start=time(16), pickup_end=time(20),
        )

    def setUp(self):
        clock = patch('order.services.timezone.localtime', return_value=datetime(
            2026, 10, 26, 10, tzinfo=ZoneInfo('Asia/Jakarta')))
        clock.start()
        self.addCleanup(clock.stop)
        self.client.force_login(self.customer)

    def reserve(self, quantity=1):
        return reserve_bag(self.customer, self.bag.pk, quantity, uuid.uuid4())

    def action_url(self, order, action):
        return reverse('order:update_api', args=[order.pk, action])

    def test_reservation_uses_real_bag_and_price_snapshots(self):
        order = self.reserve(2)
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 3)
        self.assertEqual(order.surprise_bag, self.bag)
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.total_price, Decimal('60000'))
        self.assertEqual(order.money_saved, Decimal('40000'))
        self.assertEqual(order.pickup_date.isoformat(), '2026-10-26')
        self.assertRegex(order.pickup_code, r'^[A-F0-9]{8}$')
        self.bag.discounted_price = 25000
        self.bag.save()
        order.refresh_from_db()
        self.assertEqual(order.discounted_price, Decimal('30000'))

    def test_create_post_ignores_forged_owner_price_status_and_code(self):
        response = self.client.post(reverse('order:create', args=[self.bag.pk]), {
            'quantity': 2, 'reservation_key': uuid.uuid4(), 'customer': self.other_customer.pk,
            'discounted_price': 0, 'status': 'completed', 'pickup_code': 'AAAAAAAA',
        })
        self.assertRedirects(response, reverse('order:list'))
        order = Order.objects.get()
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.discounted_price, Decimal('30000'))

    def test_retry_reservation_does_not_reduce_stock_twice(self):
        key = uuid.uuid4()
        first = reserve_bag(self.customer, self.bag.pk, 2, key)
        second = reserve_bag(self.customer, self.bag.pk, 2, key)
        self.assertEqual(first.pk, second.pk)
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 3)
        with self.assertRaises(ValidationError):
            reserve_bag(self.other_customer, self.bag.pk, 2, key)
        with self.assertRaises(ValidationError):
            reserve_bag(self.customer, self.bag.pk, 1, key)

    def test_bad_quantity_rejected(self):
        for value in ('0', '-1', '1.5', 'abc', '101', ''):
            response = self.client.post(reverse('order:create', args=[self.bag.pk]), {
                'quantity': value, 'reservation_key': uuid.uuid4(),
            })
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(Order.objects.exists())
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)

    def test_insufficient_stock_rejected_without_mutation(self):
        with self.assertRaises(ValidationError):
            self.reserve(6)
        self.assertFalse(Order.objects.exists())
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)

    def test_unavailable_bags_rejected(self):
        for changes in ({'stock': 0}, {'is_active': False}, {'pickup_end': time(9)}):
            with self.subTest(changes=changes):
                SurpriseBag.objects.filter(pk=self.bag.pk).update(**changes)
                with self.assertRaises(ValidationError):
                    self.reserve()
                SurpriseBag.objects.filter(pk=self.bag.pk).update(stock=5, is_active=True, pickup_end=time(20))
        self.assertFalse(Order.objects.exists())

    def test_failed_order_save_rolls_back_stock(self):
        with patch('order.services.Order.objects.create', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError):
                self.reserve()
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)

    def test_customer_history_is_private_in_html_and_api(self):
        own = self.reserve()
        other = reserve_bag(self.other_customer, self.bag.pk, 1, uuid.uuid4())
        response = self.client.get(reverse('order:list'))
        self.assertContains(response, str(own.pk))
        self.assertNotContains(response, str(other.pk))
        data = self.client.get(reverse('order:orders_api')).json()['html']
        self.assertIn(str(own.pk), data)
        self.assertNotIn(str(other.pk), data)
        self.assertIn(own.pickup_code, data)

    def test_merchant_only_sees_own_orders_without_pickup_secret(self):
        order = self.reserve()
        self.client.force_login(self.merchant)
        response = self.client.get(reverse('order:list'))
        self.assertContains(response, str(order.pk))
        self.assertContains(response, self.customer.username)
        self.assertNotContains(response, order.pickup_code)
        self.assertNotIn(order.pickup_code, self.client.get(reverse('order:orders_api')).json()['html'])
        self.client.force_login(self.other_merchant)
        self.assertNotContains(self.client.get(reverse('order:list')), str(order.pk))

    def test_cancel_pending_restores_stock_once_and_preserves_history(self):
        order = self.reserve(2)
        response = self.client.post(self.action_url(order, 'cancel'))
        self.assertEqual(response.json()['status'], 'cancelled')
        self.assertEqual(self.client.post(self.action_url(order, 'cancel')).status_code, 409)
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 5)
        self.assertEqual(Order.objects.count(), 1)
        self.assertFalse(ImpactLog.objects.exists())

    def test_merchant_status_flow_and_pickup_verification_without_redirect(self):
        order = self.reserve(2)
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.post(self.action_url(order, 'complete'), {'pickup_code': order.pickup_code}).status_code, 409)
        response = self.client.post(self.action_url(order, 'ready'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ready_to_pickup')
        self.assertEqual(self.client.post(self.action_url(order, 'complete'), {'pickup_code': 'Z'}).status_code, 400)
        wrong = 'FFFFFFFF' if order.pickup_code != 'FFFFFFFF' else '00000000'
        self.assertEqual(self.client.post(self.action_url(order, 'complete'), {'pickup_code': wrong}).status_code, 409)
        response = self.client.post(self.action_url(order, 'complete'), {'pickup_code': order.pickup_code.lower()})
        self.assertEqual(response.json()['status'], 'completed')
        order.refresh_from_db()
        self.assertIsNotNone(order.completed_at)
        log = ImpactLog.objects.get(order_id=order.pk)
        self.assertEqual(log.user, self.customer)
        self.assertEqual(log.money_saved, Decimal('40000'))
        self.assertEqual(log.quantity, 2)
        self.assertEqual(self.client.post(self.action_url(order, 'complete'), {'pickup_code': order.pickup_code}).status_code, 409)
        self.assertEqual(ImpactLog.objects.count(), 1)

    def test_impact_failure_rolls_back_completion(self):
        order = self.reserve()
        transition_order(self.merchant, order.pk, 'ready')
        with patch('order.services.ImpactLog.objects.get_or_create', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError):
                transition_order(self.merchant, order.pk, 'complete', order.pickup_code)
        order.refresh_from_db()
        self.assertEqual(order.status, 'ready_to_pickup')
        self.assertIsNone(order.completed_at)

    def test_cancel_after_ready_or_completed_denied(self):
        order = self.reserve()
        transition_order(self.merchant, order.pk, 'ready')
        self.assertEqual(self.client.post(self.action_url(order, 'cancel')).status_code, 409)
        transition_order(self.merchant, order.pk, 'complete', order.pickup_code)
        self.assertEqual(self.client.post(self.action_url(order, 'cancel')).status_code, 409)
        self.bag.refresh_from_db()
        self.assertEqual(self.bag.stock, 4)

    def test_other_actors_and_wrong_roles_cannot_mutate(self):
        order = self.reserve()
        for actor, action, expected in (
            (self.other_customer, 'cancel', 404), (self.other_merchant, 'ready', 404),
            (self.customer, 'ready', 403), (self.merchant, 'cancel', 403),
        ):
            self.client.force_login(actor)
            self.assertEqual(self.client.post(self.action_url(order, action)).status_code, expected)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')

    def test_guest_redirected_from_every_transaction_endpoint(self):
        order = self.reserve()
        self.client.logout()
        for url in (reverse('order:list'), reverse('order:orders_api'), reverse('order:create', args=[self.bag.pk])):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('accounts:login'), response.url)
        self.assertEqual(self.client.post(self.action_url(order, 'cancel')).status_code, 302)

    def test_profile_required_even_if_legacy_merchant_group_present(self):
        group, _ = Group.objects.get_or_create(name='Merchant')
        self.legacy.groups.add(group)
        self.client.force_login(self.legacy)
        for name in ('order:list', 'order:orders_api'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.assertEqual(self.client.get(reverse('order:create', args=[self.bag.pk])).status_code, 403)

    def test_merchant_cannot_create_orders(self):
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.post(reverse('order:create', args=[self.bag.pk]), {
            'quantity': 1, 'reservation_key': uuid.uuid4(),
        }).status_code, 403)

    def test_get_cannot_mutate_and_csrf_is_required(self):
        order = self.reserve()
        self.assertEqual(self.client.get(self.action_url(order, 'cancel')).status_code, 405)
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.customer)
        self.assertEqual(secure.post(self.action_url(order, 'cancel')).status_code, 403)
        self.assertEqual(secure.post(reverse('order:create', args=[self.bag.pk]), {}).status_code, 403)

    def test_filter_and_escaped_food_name_in_ajax(self):
        order = self.reserve()
        Order.objects.filter(pk=order.pk).update(food_name='<script>alert(1)</script>')
        html = self.client.get(reverse('order:orders_api'), {'status': 'pending'}).json()['html']
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn(str(order.pk), self.client.get(reverse('order:orders_api'), {'status': 'completed'}).json()['html'])

    def test_templates_navbar_catalog_and_auth_integration(self):
        response = self.client.get(reverse('order:list'))
        self.assertTemplateUsed(response, 'order/list.html')
        self.assertContains(response, 'id="order-dialog"')
        response = self.client.get(reverse('order:create', args=[self.bag.pk]))
        self.assertTemplateUsed(response, 'order/form.html')
        self.assertContains(response, 'name="reservation_key"')
        self.assertContains(self.client.get(reverse('surprise_bag:detail', args=[self.bag.pk])), reverse('order:create', args=[self.bag.pk]))
        self.client.force_login(self.merchant)
        self.assertEqual(self.client.get(reverse('surprise_bag:my_bags')).status_code, 200)
        self.assertContains(self.client.get(reverse('main:home')), reverse('order:list'))

    def test_bag_with_orders_is_deactivated_instead_of_deleted(self):
        self.reserve()
        with self.assertRaises(ProtectedError):
            self.bag.delete()
        self.client.force_login(self.merchant)
        response = self.client.post(reverse('surprise_bag:delete', args=[self.bag.pk]))
        self.assertEqual(response.status_code, 302)
        self.bag.refresh_from_db()
        self.assertFalse(self.bag.is_active)
        self.assertEqual(Order.objects.count(), 1)
