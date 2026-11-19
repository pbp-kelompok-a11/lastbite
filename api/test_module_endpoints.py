import uuid
from datetime import time

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from community.models import CommunityPost
from eco_impact.models import ImpactLog
from merchant_store.models import MerchantStore
from order.models import Order
from surprise_bag.models import SurpriseBag


class ModuleEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.customer = user_model.objects.create_user(username='api-customer')
        cls.other_customer = user_model.objects.create_user(username='api-other-customer')
        cls.merchant = user_model.objects.create_user(username='api-merchant')
        for user, role in (
            (cls.customer, UserProfile.Role.CUSTOMER),
            (cls.other_customer, UserProfile.Role.CUSTOMER),
            (cls.merchant, UserProfile.Role.MERCHANT),
        ):
            UserProfile.objects.create(user=user, role=role)

        cls.store = MerchantStore.objects.create(
            owner=cls.merchant, name='Toko API', opening_time=time(9), closing_time=time(20),
        )
        bag_fields = {
            'merchant': cls.merchant, 'original_price': 30000, 'discounted_price': 12000,
            'pickup_start': time(18), 'pickup_end': time(20),
        }
        cls.bag = SurpriseBag.objects.create(name='Paket tersedia', **bag_fields)
        cls.sold_out_bag = SurpriseBag.objects.create(name='Paket habis', stock=0, **bag_fields)
        cls.inactive_bag = SurpriseBag.objects.create(name='Paket nonaktif', is_active=False, **bag_fields)

        cls.orders = []
        for customer in (cls.customer, cls.other_customer):
            cls.orders.append(Order.objects.create(
                customer=customer, surprise_bag=cls.bag, food_name=cls.bag.name, quantity=1,
                original_price=30000, discounted_price=12000, pickup_date=timezone.localdate(),
                pickup_start=time(18), pickup_end=time(20), reservation_key=uuid.uuid4(),
                status=Order.Status.COMPLETED, completed_at=timezone.now(),
            ))
            ImpactLog.objects.create(
                user=customer, food_name=customer.username, original_price=30000,
                discounted_price=12000,
            )

        cls.hack = CommunityPost.objects.create(author=cls.customer, title='Simpan roti')
        cls.hack.upvotes.add(cls.other_customer)
        cls.review = CommunityPost.objects.create(
            author=cls.customer, title='Ulasan valid', post_type=CommunityPost.PostType.REVIEW,
            related_order=cls.orders[0], rating=5,
        )
        cls.unverified_review = CommunityPost.objects.create(
            author=cls.customer, title='Pesanan milik akun lain',
            post_type=CommunityPost.PostType.REVIEW, related_order=cls.orders[1], rating=5,
        )

    def get_list(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_guest_reads_available_bags_active_stores_and_community(self):
        bags = self.get_list('/api/surprise-bags/')
        bag_ids = {bag['id'] for bag in bags}
        self.assertIn(str(self.bag.pk), bag_ids)
        self.assertNotIn(str(self.sold_out_bag.pk), bag_ids)
        self.assertNotIn(str(self.inactive_bag.pk), bag_ids)
        stores = self.get_list('/api/merchant-stores/')
        self.assertIn(self.store.pk, {store['id'] for store in stores})
        hacks = self.get_list('/api/community/food-hacks/')
        hack_votes = {hack['id']: hack['upvote_count'] for hack in hacks}
        self.assertEqual(hack_votes.get(self.hack.pk), 1)
        self.assertNotIn(self.review.pk, hack_votes)
        reviews = self.get_list('/api/community/reviews/')
        review_ids = {review['id'] for review in reviews}
        self.assertIn(self.review.pk, review_ids)
        self.assertNotIn(self.unverified_review.pk, review_ids)
        self.assertNotIn(self.hack.pk, review_ids)

    def test_guest_cannot_read_private_endpoints(self):
        for path in ('/api/orders/', '/api/eco-impact/logs/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_customer_reads_only_own_orders_and_impact_logs(self):
        self.client.force_login(self.customer)
        orders = self.get_list('/api/orders/')
        self.assertEqual([order['id'] for order in orders], [str(self.orders[0].pk)])
        self.assertNotIn('pickup_code', orders[0])
        logs = self.get_list('/api/eco-impact/logs/')
        self.assertEqual([log['food_name'] for log in logs], [self.customer.username])

    def test_merchant_reads_own_orders_but_cannot_read_impact_logs(self):
        self.client.force_login(self.merchant)
        orders = self.get_list('/api/orders/')
        self.assertCountEqual([order['id'] for order in orders], [str(order.pk) for order in self.orders])
        self.assertEqual(self.client.get('/api/eco-impact/logs/').status_code, 403)
