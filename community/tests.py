import uuid
from datetime import time, timedelta


from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CommunityComment, CommunityPost
from accounts.models import UserProfile
from order.models import Order
from surprise_bag.models import SurpriseBag


def completed_order(customer, merchant=None, **changes):
    if merchant is None:
        merchant, _ = get_user_model().objects.get_or_create(username=f'merchant_for_{customer.pk}')
    bag = SurpriseBag.objects.create(
        merchant=merchant, name='Paket Roti Sore', description='Pilihan roti.',
        original_price=50000, discounted_price=30000, stock=5,
        pickup_start=time(16), pickup_end=time(20),
    )
    data = dict(customer=customer, surprise_bag=bag, food_name=bag.name,
                quantity=1, original_price=bag.original_price, discounted_price=bag.discounted_price,
                pickup_date=timezone.localdate(), pickup_start=bag.pickup_start, pickup_end=bag.pickup_end,
                reservation_key=uuid.uuid4(), status=Order.Status.COMPLETED, completed_at=timezone.now())
    data.update(changes)
    return Order.objects.create(**data)


class CommunityFeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='food_hack_writer')

    def create_post(self, **changes):
        fields = {
            'author': self.author, 'title': 'Tips menyimpan roti',
            'content': 'Bekukan roti dalam wadah tertutup.',
            'post_type': CommunityPost.PostType.FOOD_HACK,
        }
        fields.update(changes)
        post = CommunityPost(**fields)
        post.full_clean()
        post.save()
        return post

    def test_guest_sees_food_hacks_and_reviews_newest_first(self):
        older = self.create_post(title='Tips roti lama')
        CommunityPost.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=1))
        newer = self.create_post(title='Tips sayur baru')
        # Data demo dari sebelum migration tetap dapat dibaca, tanpa klaim terverifikasi.
        review = CommunityPost.objects.create(author=self.author, title='Review masuk feed ini',
                                               content='Review lama.', post_type='review', rating=5)
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertEqual(list(response.context['posts']), [review, newer, older])
        self.assertContains(response, 'food_hack_writer')
        self.assertContains(response, 'Bekukan roti dalam wadah tertutup.')
        self.assertContains(response, review.title)
        self.assertContains(response, 'Belum terverifikasi')

    def test_empty_feed(self):
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Belum ada postingan')
        self.assertQuerySetEqual(response.context['posts'], [])

    def test_database_title_update_appears_on_refresh(self):
        post = self.create_post(title='Judul sebelum edit')
        self.assertContains(self.client.get(reverse('community:home')), 'Judul sebelum edit')
        post.title = 'Judul setelah edit'
        post.full_clean()
        post.save()
        response = self.client.get(reverse('community:home'))
        self.assertContains(response, 'Judul setelah edit')
        self.assertNotContains(response, 'Judul sebelum edit')

    def test_user_content_is_escaped(self):
        self.create_post(title='<script>alert(1)</script>', content='<b>Konten pengguna</b>')
        response = self.client.get(reverse('community:home'))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;b&gt;Konten pengguna&lt;/b&gt;')

    def test_feed_only_accepts_read_requests(self):
        self.assertEqual(self.client.head(reverse('community:home')).status_code, 200)
        self.assertEqual(self.client.post(reverse('community:home')).status_code, 405)
        self.assertFalse(CommunityPost.objects.exists())


class CommunityFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = get_user_model().objects.create_user(username='filter_writer')
        cls.bread = CommunityPost.objects.create(author=author, title='Tips ROTI', content='Bekukan dalam wadah.')
        cls.vegetable = CommunityPost.objects.create(author=author, title='Tips sayur', content='Olah sisa brokoli.')
        cls.review = CommunityPost.objects.create(author=author, title='Review roti', content='Enak.', post_type='review', rating=5)

    def test_search_matches_title_or_content_ignoring_case(self):
        for query, expected in (('roti', self.bread), ('BROKOLI', self.vegetable), ('  wadah  ', self.bread)):
            with self.subTest(query=query):
                response = self.client.get(reverse('community:home'), {'q': query, 'post_type': 'food_hack'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(list(response.context['posts']), [expected])
                self.assertEqual(response.context['query'], query.strip())

    def test_ajax_returns_filtered_fragment_without_page_layout(self):
        response = self.client.get(reverse('community:home'), {'q': 'roti'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/components/feed_results.html')
        self.assertContains(response, 'id="community-results"')
        self.assertContains(response, self.bread.title)
        self.assertNotContains(response, self.vegetable.title)
        self.assertNotContains(response, '<html')
        self.assertNotContains(response, '<script')
        self.assertIn('X-Requested-With', response.headers['Vary'])

    def test_ajax_handles_empty_results_and_escapes_input(self):
        response = self.client.get(reverse('community:home'), {'q': '<script>alert(1)</script>'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Tidak ada hasil yang cocok')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_tabs_filter_post_types(self):
        for post_type, expected in (
            ('all', {self.bread, self.vegetable, self.review}),
            ('food_hack', {self.bread, self.vegetable}),
            ('review', {self.review}),
        ):
            with self.subTest(post_type=post_type):
                response = self.client.get(reverse('community:home'), {'post_type': post_type})
                self.assertEqual(response.context['selected_post_type'], post_type)
                self.assertEqual(set(response.context['posts']), expected)
                self.assertContains(response, 'class="community-tab community-tab--active"', count=1)
                label = {'all': 'All Posts', 'food_hack': 'Food Hacks', 'review': 'Reviews'}[post_type]
                self.assertContains(response, f'href="{reverse("community:home")}?post_type={post_type}" aria-current="page">{label}</a>')

    def test_search_is_combined_with_category_and_keeps_newest_order(self):
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'q': 'Tips'})
        self.assertEqual(list(response.context['posts']), [self.vegetable, self.bread])
        self.assertContains(response, 'name="post_type" value="food_hack"')
        self.assertContains(response, 'name="q" value="Tips"')
        self.assertContains(response, '?post_type=all&amp;q=Tips')

    def test_no_matches_differs_from_empty_feed(self):
        response = self.client.get(reverse('community:home'), {'q': 'tidakada123'})
        self.assertContains(response, 'Tidak ada hasil yang cocok')
        self.assertNotContains(response, 'Belum ada Food Hack')
        self.assertQuerySetEqual(response.context['posts'], [])

    def test_invalid_category_and_blank_search_fall_back_safely(self):
        response = self.client.get(reverse('community:home'), {'post_type': 'invalid', 'q': '   '})
        self.assertEqual(response.context['selected_post_type'], 'all')
        self.assertEqual(response.context['query'], '')
        self.assertEqual(set(response.context['posts']), {self.bread, self.vegetable, self.review})

    def test_search_text_is_escaped_and_tab_query_is_url_encoded(self):
        response = self.client.get(reverse('community:home'), {'q': '<script>& test'})
        self.assertContains(response, '&lt;script&gt;&amp; test')
        self.assertNotContains(response, '<script>& test')
        self.assertContains(response, 'q=%3Cscript%3E%26+test')


class CommunityDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = get_user_model().objects.create_user(username='detail_writer')
        cls.first = CommunityPost.objects.create(
            author=author, title='Tips roti', content='Paragraf pertama.\n\nParagraf kedua.',
        )
        cls.second = CommunityPost.objects.create(
            author=author, title='Tips sayur', content='Konten sayur yang berbeda.',
        )
        cls.review = CommunityPost.objects.create(
            author=author, post_type='review', rating=5, title='Review', content='Ulasan.',
        )

    def test_cards_link_to_their_own_details(self):
        response = self.client.get(reverse('community:home'))
        for post in (self.first, self.second):
            self.assertContains(response, 'href="{}?feed='.format(
                reverse('community:post_detail', args=[post.pk])
            ))

    def test_detail_back_link_preserves_feed_page_sort_search_and_liked_filter(self):
        feed_query = 'post_type=food_hack&sort=oldest&liked=1&q=roti+%26+telur&page=20'
        response = self.client.get(reverse('community:post_detail', args=[self.first.pk]), {'feed': feed_query})
        self.assertEqual(response.context['back_url'], reverse('community:home') + '?' + feed_query)
        self.assertContains(response, 'page=20')

    def test_direct_detail_back_link_defaults_to_community(self):
        response = self.client.get(reverse('community:post_detail', args=[self.first.pk]))
        self.assertEqual(response.context['back_url'], reverse('community:home'))

    def test_guest_sees_the_requested_post_and_full_content(self):
        for post, other in ((self.first, self.second), (self.second, self.first)):
            with self.subTest(post=post.pk):
                response = self.client.get(reverse('community:post_detail', args=[post.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'community/food_hack_detail.html')
                self.assertTemplateUsed(response, 'base.html')
                self.assertEqual(response.context['post'], post)
                self.assertContains(response, post.title)
                self.assertNotContains(response, other.title)
                self.assertContains(response, 'detail_writer')
                self.assertContains(response, '<time datetime=')
                self.assertContains(response, reverse('community:home'))
        response = self.client.get(reverse('community:post_detail', args=[self.first.pk]))
        self.assertContains(response, '<p>Paragraf pertama.</p>')
        self.assertContains(response, '<p>Paragraf kedua.</p>')

    def test_missing_post_and_review_return_404(self):
        for pk in (999999, self.review.pk):
            with self.subTest(pk=pk):
                self.assertEqual(self.client.get(reverse('community:post_detail', args=[pk])).status_code, 404)

    def test_detail_escapes_user_content(self):
        self.first.title = '<script>alert(1)</script>'
        self.first.content = '<img src=x onerror=alert(1)>'
        self.first.save()
        response = self.client.get(reverse('community:post_detail', args=[self.first.pk]))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')

    def test_detail_is_read_only(self):
        url = reverse('community:post_detail', args=[self.first.pk])
        self.assertEqual(self.client.head(url).status_code, 200)
        self.assertEqual(self.client.post(url, {'title': 'Diubah'}).status_code, 405)
        self.first.refresh_from_db()
        self.assertEqual(self.first.title, 'Tips roti')


class FoodHackCreateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='customer', password='test-password-123')
        UserProfile.objects.create(user=cls.author, role=UserProfile.Role.CUSTOMER)
        cls.other = get_user_model().objects.create_user(username='other')

    def test_guest_redirects_to_working_login_and_cannot_post(self):
        url = reverse('community:food_hack_create')
        for method in (self.client.get, self.client.post):
            response = method(url)
            self.assertRedirects(response, reverse('accounts:login') + '?next=' + url)
        self.assertFalse(CommunityPost.objects.exists())

    def test_login_returns_user_to_create_form(self):
        url = reverse('community:food_hack_create')
        response = self.client.post(reverse('accounts:login') + '?next=' + url, {
            'username': 'customer', 'password': 'test-password-123', 'next': url,
        })
        self.assertRedirects(response, url)

    def test_authenticated_get_displays_form_without_saving(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('community:food_hack_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/food_hack_form.html')
        self.assertEqual(list(response.context['form'].fields), ['title', 'content'])
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertFalse(CommunityPost.objects.exists())

    def test_valid_post_sets_protected_fields_and_appears_in_detail_and_feed(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('community:food_hack_create'), {
            'title': 'Tips freezer', 'content': 'Simpan dalam porsi kecil.',
            'author': self.other.pk, 'post_type': 'review', 'rating': 5,
        })
        post = CommunityPost.objects.get()
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.post_type, 'food_hack')
        self.assertIsNone(post.rating)
        self.assertRedirects(response, reverse('community:post_detail', args=[post.pk]))
        self.assertContains(self.client.get(reverse('community:home')), 'Tips freezer')
        self.assertContains(self.client.get(response.url), 'Simpan dalam porsi kecil.')

    def test_invalid_post_shows_errors_and_keeps_input(self):
        self.client.force_login(self.author)
        for data, field in (({'title': '   ', 'content': 'Konten tetap'}, 'title'),
                            ({'title': 'Judul tetap', 'content': '   '}, 'content'),
                            ({'title': 'a' * 256, 'content': 'Konten tetap'}, 'title')):
            with self.subTest(field=field, data=data):
                response = self.client.post(reverse('community:food_hack_create'), data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.assertEqual(response.context['form'].data['title'], data['title'])
                self.assertFalse(CommunityPost.objects.exists())

    def test_create_requires_csrf_and_rejects_other_methods(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.author)
        url = reverse('community:food_hack_create')
        self.assertEqual(client.post(url, {'title': 'Tips', 'content': 'Konten'}).status_code, 403)
        self.client.force_login(self.author)
        self.assertEqual(self.client.put(url).status_code, 405)
        self.assertFalse(CommunityPost.objects.exists())

    def test_bad_login_and_external_next_are_not_accepted(self):
        url = reverse('accounts:login')
        response = self.client.post(url, {'username': 'customer', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        response = self.client.post(url, {
            'username': 'customer', 'password': 'test-password-123',
            'next': 'https://example.org/',
        })
        self.assertRedirects(response, reverse('main:home'))


class FoodHackOwnershipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username='post_owner')
        cls.other = get_user_model().objects.create_user(username='not_owner')
        UserProfile.objects.create(user=cls.owner, role=UserProfile.Role.CUSTOMER)
        UserProfile.objects.create(user=cls.other, role=UserProfile.Role.CUSTOMER)
        cls.post = CommunityPost.objects.create(author=cls.owner, title='Judul awal', content='Konten awal')
        cls.review = CommunityPost.objects.create(
            author=cls.owner, title='Review', content='Ulasan', post_type='review', rating=5,
        )

    def url(self, action, pk=None):
        return reverse('community:post_' + action, args=[pk if pk is not None else self.post.pk])

    def test_guest_redirected_for_edit_and_delete(self):
        for action in ('edit', 'delete'):
            for method in (self.client.get, self.client.post):
                with self.subTest(action=action, method=method.__name__):
                    response = method(self.url(action))
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
        self.assertTrue(CommunityPost.objects.filter(pk=self.post.pk).exists())

    def test_other_user_cannot_read_or_mutate_owner_post(self):
        self.client.force_login(self.other)
        for action in ('edit', 'delete'):
            for method in (self.client.get, self.client.post):
                with self.subTest(action=action, method=method.__name__):
                    self.assertEqual(method(self.url(action), {'title': 'Diserang', 'content': 'Baru'}).status_code, 404)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Judul awal')

    def test_owner_gets_prefilled_edit_and_can_save_only_allowed_fields(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url('edit'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Judul awal"')
        self.assertEqual(response.context['form'].instance, self.post)
        created_at = self.post.created_at
        response = self.client.post(self.url('edit'), {
            'title': 'Judul diperbarui', 'content': 'Konten diperbarui',
            'author': self.other.pk, 'post_type': 'review', 'rating': 5,
        })
        self.assertRedirects(response, reverse('community:post_detail', args=[self.post.pk]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Judul diperbarui')
        self.assertEqual(self.post.content, 'Konten diperbarui')
        self.assertEqual(self.post.author, self.owner)
        self.assertEqual(self.post.post_type, 'food_hack')
        self.assertIsNone(self.post.rating)
        self.assertEqual(self.post.created_at, created_at)
        self.assertGreaterEqual(self.post.updated_at, self.post.created_at)

    def test_invalid_edit_does_not_change_database(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url('edit'), {'title': '   ', 'content': 'Konten baru'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Judul awal')
        self.assertEqual(self.post.content, 'Konten awal')

    def test_delete_get_only_confirms_and_post_deletes(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url('delete'))
        self.assertTemplateUsed(response, 'community/food_hack_confirm_delete.html')
        self.assertContains(response, 'Judul awal')
        self.assertTrue(CommunityPost.objects.filter(pk=self.post.pk).exists())
        self.assertRedirects(self.client.post(self.url('delete')), reverse('community:home'))
        self.assertFalse(CommunityPost.objects.filter(pk=self.post.pk).exists())
        self.assertEqual(self.client.get(reverse('community:post_detail', args=[self.post.pk])).status_code, 404)

    def test_review_and_missing_post_are_not_editable_or_deletable(self):
        self.client.force_login(self.owner)
        for pk in (self.review.pk, 999999):
            for action in ('edit', 'delete'):
                for method in (self.client.get, self.client.post):
                    with self.subTest(pk=pk, action=action, method=method.__name__):
                        self.assertEqual(method(self.url(action, pk)).status_code, 404)

    def test_csrf_and_http_methods_are_enforced(self):
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(self.owner)
        self.client.force_login(self.owner)
        for action in ('edit', 'delete'):
            self.assertEqual(secure_client.post(self.url(action)).status_code, 403)
            self.assertEqual(self.client.put(self.url(action)).status_code, 405)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Judul awal')

    def test_management_links_visible_only_to_owner(self):
        url = reverse('community:post_detail', args=[self.post.pk])
        self.assertNotContains(self.client.get(url), self.url('edit'))
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(url), self.url('delete'))
        self.client.force_login(self.owner)
        response = self.client.get(url)
        self.assertContains(response, self.url('edit'))
        self.assertContains(response, self.url('delete'))


class CommunityAccountsIntegrationTests(TestCase):
    def test_registration_login_next_and_food_hack_crud(self):
        create_url = reverse('community:food_hack_create')
        response = self.client.get(create_url)
        self.assertRedirects(response, reverse('accounts:login') + '?next=' + create_url)
        self.client.post(reverse('accounts:register'), {
            'username': 'integrated_customer', 'role': 'customer',
            'password1': 'LastBite-Test-937!', 'password2': 'LastBite-Test-937!',
        })
        response = self.client.post(reverse('accounts:login'), {
            'username': 'integrated_customer', 'password': 'LastBite-Test-937!', 'next': create_url,
        })
        self.assertRedirects(response, create_url)
        response = self.client.post(create_url, {'title': 'Tips integrasi', 'content': 'Konten integrasi.'})
        post = CommunityPost.objects.get()
        self.assertRedirects(response, reverse('community:post_detail', args=[post.pk]))
        self.assertContains(self.client.get(reverse('community:home')), 'Tips integrasi')
        response = self.client.post(reverse('community:post_edit', args=[post.pk]), {
            'title': 'Tips sudah diedit', 'content': 'Konten baru.',
        })
        self.assertRedirects(response, reverse('community:post_detail', args=[post.pk]))
        self.assertRedirects(self.client.post(reverse('community:post_delete', args=[post.pk])), reverse('community:home'))
        self.assertFalse(CommunityPost.objects.exists())

    def test_account_without_profile_cannot_write(self):
        user = get_user_model().objects.create_user(username='without_profile')
        post = CommunityPost.objects.create(author=user, title='Tetap utuh', content='Konten.')
        self.client.force_login(user)
        urls = [reverse('community:food_hack_create'),
                reverse('community:post_edit', args=[post.pk]),
                reverse('community:post_delete', args=[post.pk])]
        for url in urls:
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(url, {'title': 'Diubah', 'content': 'Baru'}).status_code, 403)
        self.assertNotContains(self.client.get(reverse('community:home')), 'Bagikan Food Hack')
        detail = self.client.get(reverse('community:post_detail', args=[post.pk]))
        self.assertNotContains(detail, 'Edit Food Hack')
        self.assertNotContains(detail, 'Hapus Food Hack')
        post.refresh_from_db()
        self.assertEqual(post.title, 'Tetap utuh')

    def test_old_community_login_is_removed(self):
        self.assertEqual(self.client.get('/community/login/').status_code, 404)


class MerchantFoodHackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.merchant = get_user_model().objects.create_user(username='food_hack_merchant')
        UserProfile.objects.create(user=cls.merchant, role=UserProfile.Role.MERCHANT)
        cls.customer = get_user_model().objects.create_user(username='food_hack_customer')
        UserProfile.objects.create(user=cls.customer, role=UserProfile.Role.CUSTOMER)
        cls.other_merchant = get_user_model().objects.create_user(username='other_merchant')
        UserProfile.objects.create(user=cls.other_merchant, role=UserProfile.Role.MERCHANT)

    def test_merchant_sees_create_form_and_can_publish_with_server_assigned_author(self):
        self.client.force_login(self.merchant)
        self.assertContains(self.client.get(reverse('community:home')), 'Bagikan Food Hack')
        url = reverse('community:food_hack_create')
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {
            'title': 'Tips dari merchant', 'content': 'Ide dari dapur toko.',
            'author': self.customer.pk, 'post_type': 'review', 'rating': 5,
        })
        post = CommunityPost.objects.get()
        self.assertRedirects(response, reverse('community:post_detail', args=[post.pk]))
        self.assertEqual(post.author, self.merchant)
        self.assertEqual(post.post_type, 'food_hack')
        self.assertIsNone(post.rating)

    def test_merchant_can_edit_and_delete_own_post(self):
        post = CommunityPost.objects.create(author=self.merchant, title='Tips toko', content='Konten.')
        self.client.force_login(self.merchant)
        detail = self.client.get(reverse('community:post_detail', args=[post.pk]))
        self.assertContains(detail, 'Edit Food Hack')
        self.assertContains(detail, 'Hapus Food Hack')
        edit_url = reverse('community:post_edit', args=[post.pk])
        self.assertContains(self.client.get(edit_url), 'Tips toko')
        self.client.post(edit_url, {'title': 'Tips diperbarui', 'content': 'Konten baru.'})
        post.refresh_from_db()
        self.assertEqual(post.title, 'Tips diperbarui')
        delete_url = reverse('community:post_delete', args=[post.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.assertTrue(CommunityPost.objects.filter(pk=post.pk).exists())
        self.assertRedirects(self.client.post(delete_url), reverse('community:home'))
        self.assertFalse(CommunityPost.objects.filter(pk=post.pk).exists())

    def test_customer_and_other_merchant_cannot_edit_or_delete_merchant_post(self):
        post = CommunityPost.objects.create(author=self.merchant, title='Tips pemilik', content='Konten.')
        for user in (self.customer, self.other_merchant):
            self.client.force_login(user)
            for action in ('post_edit', 'post_delete'):
                url = reverse('community:' + action, args=[post.pk])
                for method in (self.client.get, self.client.post):
                    with self.subTest(user=user.username, action=action, method=method.__name__):
                        self.assertEqual(method(url, {'title': 'Diubah', 'content': 'Baru.'}).status_code, 404)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Tips pemilik')

    def test_merchant_cannot_manage_customer_post(self):
        post = CommunityPost.objects.create(author=self.customer, title='Tips customer', content='Konten.')
        self.client.force_login(self.merchant)
        for action in ('post_edit', 'post_delete'):
            url = reverse('community:' + action, args=[post.pk])
            self.assertEqual(self.client.post(url, {'title': 'Diubah', 'content': 'Baru.'}).status_code, 404)

    def test_merchant_badge_visible_to_guests_in_feed_ajax_and_detail(self):
        post = CommunityPost.objects.create(author=self.merchant, title='Tips merchant', content='Konten.')
        customer_post = CommunityPost.objects.create(author=self.customer, title='Tips customer', content='Konten.')
        for url, headers in (
            (reverse('community:home'), {}),
            (reverse('community:home'), {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}),
            (reverse('community:post_detail', args=[post.pk]), {}),
        ):
            response = self.client.get(url, **headers)
            self.assertContains(response, 'food-hack-card__badge--merchant', count=1)
        response = self.client.get(reverse('community:post_detail', args=[customer_post.pk]))
        self.assertNotContains(response, 'food-hack-card__badge--merchant')

    def test_empty_merchant_post_is_rejected(self):
        self.client.force_login(self.merchant)
        response = self.client.post(reverse('community:food_hack_create'), {'title': ' ', 'content': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertFalse(CommunityPost.objects.exists())


class CommunityPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='pagination_author')
        CommunityPost.objects.bulk_create([
            CommunityPost(author=cls.author, title=f'Tips roti {number}', content='Simpan roti.')
            for number in range(23)
        ])
        CommunityPost.objects.create(
            author=cls.author, title='Review roti', content='Enak.', post_type='review', rating=5,
        )

    def test_pages_have_ten_posts_and_preserve_newest_order_without_overlap(self):
        actual = []
        for page, expected_count in ((1, 10), (2, 10), (3, 4)):
            response = self.client.get(reverse('community:home'), {'page': page})
            posts = list(response.context['posts'])
            self.assertEqual(len(posts), expected_count)
            self.assertEqual(response.context['page_obj'].paginator.count, 24)
            actual.extend(post.pk for post in posts)
        expected = list(CommunityPost.objects.values_list('pk', flat=True))
        self.assertEqual(actual, expected)

    def test_links_preserve_filter_and_encoded_search(self):
        response = self.client.get(reverse('community:home'), {
            'post_type': 'food_hack', 'q': 'Tips roti', 'page': 2,
        })
        self.assertContains(response, '?post_type=food_hack&amp;q=Tips+roti&amp;page=3')
        self.assertContains(response, 'Halaman 2 dari 3')
        self.assertContains(response, 'aria-label="Halaman sebelumnya"')

    def test_ajax_page_uses_same_pagination(self):
        response = self.client.get(reverse('community:home'), {'page': 3},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, 'community/components/feed_results.html')
        self.assertContains(response, 'data-page="3"')
        self.assertEqual(len(response.context['posts']), 4)
        self.assertNotContains(response, 'aria-label="Halaman berikutnya"')

    def test_invalid_page_is_handled(self):
        for requested, expected in (('oops', 1), ('999', 3), ('0', 3)):
            with self.subTest(page=requested):
                response = self.client.get(reverse('community:home'), {'page': requested})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['page_obj'].number, expected)

    def test_single_page_and_empty_search_show_only_page_one(self):
        for query in ('Tips roti 22', 'no matching post'):
            with self.subTest(query=query):
                response = self.client.get(reverse('community:home'), {'q': query})
                self.assertContains(response, 'aria-label="Halaman postingan"')
                self.assertContains(response, 'Halaman 1 dari 1')
                self.assertContains(response, 'aria-label="Halaman 1"')
                self.assertNotContains(response, 'aria-label="Halaman sebelumnya"')
                self.assertNotContains(response, 'aria-label="Halaman berikutnya"')
                self.assertNotContains(response, 'data-page-link=')
                self.assertEqual(response.context['page_obj'].number, 1)

    def test_navigation_buttons_follow_page_position(self):
        for page, previous, following in ((1, False, True), (2, True, True), (3, True, False)):
            with self.subTest(page=page):
                response = self.client.get(reverse('community:home'), {'page': page})
                self.assertEqual('aria-label="Halaman sebelumnya"' in response.content.decode(), previous)
                self.assertEqual('aria-label="Halaman berikutnya"' in response.content.decode(), following)

    def test_hundred_pages_show_compact_numbers_at_start_middle_and_end(self):
        CommunityPost.objects.bulk_create([
            CommunityPost(author=self.author, title=f'Extra tips {number}', content='Konten.')
            for number in range(976)
        ])
        for page, visible, hidden, ellipses in (
            (1, (2, 3, 100), (4, 50, 99), 1),
            (6, (1, 4, 5, 7, 8, 100), (2, 3, 9, 99), 2),
            (50, (1, 48, 49, 51, 52, 100), (2, 47, 53, 99), 2),
            (100, (1, 98, 99), (2, 50, 97), 1),
        ):
            with self.subTest(page=page):
                response = self.client.get(reverse('community:home'), {'page': page})
                self.assertContains(response, 'Halaman ' + str(page) + ' dari 100')
                self.assertContains(response, 'community-page--ellipsis', count=ellipses)
                for number in visible:
                    self.assertContains(response, f'data-page-link="{number}"')
                for number in hidden:
                    self.assertNotContains(response, f'data-page-link="{number}"')


class CommunitySortAndLikedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(username='sort_customer')
        cls.other = get_user_model().objects.create_user(username='sort_other')
        UserProfile.objects.create(user=cls.customer, role=UserProfile.Role.CUSTOMER)
        UserProfile.objects.create(user=cls.other, role=UserProfile.Role.CUSTOMER)
        cls.older = CommunityPost.objects.create(author=cls.customer, title='Tips roti lama', content='Konten.')
        cls.popular = CommunityPost.objects.create(author=cls.customer, title='Tips roti populer', content='Konten.')
        cls.newer = CommunityPost.objects.create(author=cls.customer, title='Tips nasi baru', content='Konten.')
        cls.popular.upvotes.add(cls.customer, cls.other)
        cls.older.upvotes.add(cls.customer)

    def test_sort_modes_use_dates_or_total_likes(self):
        for sort, expected in (
            ('newest', [self.newer, self.popular, self.older]),
            ('oldest', [self.older, self.popular, self.newer]),
            ('likes', [self.popular, self.older, self.newer]),
            ('invalid', [self.newer, self.popular, self.older]),
        ):
            with self.subTest(sort=sort):
                response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'sort': sort})
                self.assertEqual(list(response.context['posts']), expected)

    def test_equal_dates_and_likes_have_stable_order(self):
        CommunityPost.objects.update(created_at=timezone.now())
        self.newer.upvotes.add(self.other)
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'sort': 'likes'})
        self.assertEqual(list(response.context['posts']), [self.popular, self.newer, self.older])

    def test_liked_filter_only_uses_current_user_and_keeps_total_counts(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1', 'sort': 'likes'})
        self.assertEqual(list(response.context['posts']), [self.popular, self.older])
        self.assertEqual(response.context['posts'][0].upvote_count, 2)
        self.client.force_login(self.other)
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'})
        self.assertEqual(list(response.context['posts']), [self.popular])

    def test_search_sort_and_liked_filters_work_together_in_ajax(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('community:home'), {
            'liked': '1', 'sort': 'oldest', 'q': 'roti', 'post_type': 'food_hack',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(list(response.context['posts']), [self.older, self.popular])
        self.assertContains(response, 'data-sort="oldest" data-liked="1"')
        self.assertContains(response, '?post_type=food_hack&amp;sort=oldest&amp;liked=1">Hapus pencarian')

    def test_liked_filter_pagination_preserves_all_filters(self):
        for number in range(12):
            post = CommunityPost.objects.create(author=self.customer, title=f'Tips roti {number}', content='Konten.')
            post.upvotes.add(self.customer)
        self.client.force_login(self.customer)
        response = self.client.get(reverse('community:home'), {
            'liked': '1', 'sort': 'oldest', 'q': 'roti', 'post_type': 'food_hack', 'page': 2,
        })
        self.assertEqual(response.context['page_obj'].paginator.count, 14)
        self.assertEqual(len(response.context['posts']), 4)
        self.assertContains(response, '?post_type=food_hack&amp;sort=oldest&amp;liked=1&amp;q=roti&amp;page=1')

    def test_guest_liked_filter_redirects_to_login_and_ajax_returns_login_url(self):
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 401)
        self.assertIn('login_url', response.json())

    def test_empty_liked_state_after_unlike_and_toggle_off(self):
        self.client.force_login(self.other)
        self.client.post(reverse('community:post_upvote', args=[self.popular.pk]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'})
        self.assertContains(response, 'Belum ada postingan yang disukai')
        self.assertEqual(len(response.context['posts']), 0)
        self.assertEqual(len(self.client.get(reverse('community:home')).context['posts']), 3)


class CommunityUpvoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(username='voting_customer')
        UserProfile.objects.create(user=cls.customer, role=UserProfile.Role.CUSTOMER)
        cls.other = get_user_model().objects.create_user(username='other_voter')
        UserProfile.objects.create(user=cls.other, role=UserProfile.Role.CUSTOMER)
        cls.post = CommunityPost.objects.create(author=cls.customer, title='Tips upvote', content='Konten.')
        cls.url = reverse('community:post_upvote', args=[cls.post.pk])

    def vote(self, **kwargs):
        return self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', **kwargs)

    def test_toggle_adds_then_removes_vote_in_database(self):
        self.client.force_login(self.customer)
        response = self.vote()
        self.assertEqual(response.json(), {'post_id': self.post.pk, 'has_upvoted': True, 'upvote_count': 1})
        self.assertTrue(self.post.upvotes.filter(pk=self.customer.pk).exists())
        response = self.vote()
        self.assertEqual(response.json()['upvote_count'], 0)
        self.assertFalse(response.json()['has_upvoted'])
        self.assertFalse(self.post.upvotes.exists())

    def test_each_customer_has_one_independent_vote(self):
        self.post.upvotes.add(self.customer, self.customer)
        self.assertEqual(self.post.upvotes.count(), 1)
        self.client.force_login(self.other)
        self.assertEqual(self.vote().json()['upvote_count'], 2)
        self.assertEqual(self.vote().json()['upvote_count'], 1)
        self.assertTrue(self.post.upvotes.filter(pk=self.customer.pk).exists())

    def test_guest_is_rejected_and_receives_shared_login_url(self):
        response = self.vote()
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.json()['login_url'].startswith(reverse('accounts:login') + '?next='))
        self.assertFalse(self.post.upvotes.exists())

    def test_user_without_profile_is_rejected(self):
        user = get_user_model().objects.create_user(username='voter_without_profile')
        self.client.force_login(user)
        self.assertEqual(self.vote().status_code, 403)
        self.assertFalse(self.post.upvotes.exists())

    def test_merchant_can_like_filter_liked_posts_and_unlike(self):
        user = get_user_model().objects.create_user(username='merchant_voter')
        UserProfile.objects.create(user=user, role=UserProfile.Role.MERCHANT)
        self.client.force_login(user)
        for url in (reverse('community:home'), reverse('community:post_detail', args=[self.post.pk])):
            self.assertContains(self.client.get(url), 'data-upvote-form')
        response = self.vote()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['has_upvoted'])
        self.assertEqual(response.json()['upvote_count'], 1)
        self.assertTrue(self.post.upvotes.filter(pk=user.pk).exists())
        liked_feed = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'})
        self.assertEqual(list(liked_feed.context['posts']), [self.post])
        self.assertContains(liked_feed, 'aria-pressed="true"')
        self.assertFalse(self.vote().json()['has_upvoted'])
        self.assertFalse(self.post.upvotes.exists())
        self.assertQuerySetEqual(self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'liked': '1'}).context['posts'], [])

    def test_get_does_not_toggle(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertFalse(self.post.upvotes.exists())

    def test_review_and_missing_post_cannot_be_upvoted(self):
        review = CommunityPost.objects.create(author=self.customer, title='Review', content='Enak.', post_type='review', rating=5)
        self.client.force_login(self.customer)
        for pk in (review.pk, review.pk + 1000):
            with self.subTest(pk=pk):
                response = self.client.post(reverse('community:post_upvote', args=[pk]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 404)
        self.assertFalse(review.upvotes.exists())

    def test_csrf_token_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        self.assertEqual(client.post(self.url).status_code, 403)
        self.assertFalse(self.post.upvotes.exists())
        client.get(reverse('community:post_detail', args=[self.post.pk]))
        token = client.cookies['csrftoken'].value
        response = client.post(self.url, HTTP_X_CSRFTOKEN=token, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.upvotes.count(), 1)

    def test_feed_detail_and_ajax_keep_saved_count_and_current_user_state(self):
        self.post.upvotes.add(self.customer)
        self.client.force_login(self.customer)
        for url, headers in (
            (reverse('community:home'), {}),
            (reverse('community:home'), {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}),
            (reverse('community:post_detail', args=[self.post.pk]), {}),
        ):
            with self.subTest(url=url, headers=headers):
                response = self.client.get(url, **headers)
                self.assertContains(response, 'aria-pressed="true"')
                self.assertContains(response, '<span data-upvote-count>1</span>', html=True)
        self.client.force_login(self.other)
        response = self.client.get(reverse('community:post_detail', args=[self.post.pk]))
        self.assertContains(response, 'aria-pressed="false"')
        self.assertContains(response, '<span data-upvote-count>1</span>', html=True)

    def test_guest_sees_login_link_instead_of_voting_form(self):
        response = self.client.get(reverse('community:home'))
        self.assertContains(response, 'Login untuk like: Tips upvote')
        self.assertNotContains(response, 'data-upvote-form')

    def test_form_without_javascript_redirects_to_detail(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('community:post_detail', args=[self.post.pk]))
        self.assertEqual(self.post.upvotes.count(), 1)


class CommunityCommentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(username='comment_customer')
        UserProfile.objects.create(user=cls.customer, role='customer')
        cls.merchant = get_user_model().objects.create_user(username='comment_merchant')
        UserProfile.objects.create(user=cls.merchant, role='merchant')
        cls.other = get_user_model().objects.create_user(username='comment_other')
        UserProfile.objects.create(user=cls.other, role='customer')
        cls.post = CommunityPost.objects.create(author=cls.customer, title='Tips komentar', content='Konten.')
        cls.other_post = CommunityPost.objects.create(author=cls.other, title='Post lain', content='Konten.')
        cls.review = CommunityPost.objects.create(author=cls.customer, title='Review', content='Enak.', post_type='review', rating=5)

    def url(self, action='create', comment=None, post=None):
        args = [post.pk if post is not None else self.post.pk]
        if comment is not None:
            args.append(comment.pk)
        return reverse('community:comment_' + action, args=args)

    def test_customer_and_merchant_can_comment_with_server_assigned_parent_and_author(self):
        for user in (self.customer, self.merchant):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(self.url(), {
                    'comment-content': '  Pengalaman memasak saya.  ',
                    'author': self.other.pk, 'post': self.review.pk,
                })
                self.assertEqual(response.status_code, 302)
                comment = CommunityComment.objects.latest('pk')
                self.assertEqual(comment.author, user)
                self.assertEqual(comment.post, self.post)
                self.assertEqual(comment.content, 'Pengalaman memasak saya.')
                detail = self.client.get(response.url)
                self.assertContains(detail, 'Pengalaman memasak saya.')

    def test_ajax_create_returns_saved_comment_fragment(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url(), {'comment-content': 'Ide yang menarik!'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ide yang menarik!')
        self.assertContains(response, 'id="comments"')
        self.assertNotContains(response, '<html')
        self.assertEqual(CommunityComment.objects.count(), 1)

    def test_guest_can_read_comments_but_cannot_create_edit_or_delete(self):
        comment = CommunityComment.objects.create(post=self.post, author=self.customer, content='Komentar publik.')
        detail = self.client.get(reverse('community:post_detail', args=[self.post.pk]))
        self.assertContains(detail, 'Komentar publik.')
        self.assertContains(detail, 'untuk ikut berkomentar.')
        self.assertNotContains(detail, 'data-comment-form=')
        for action in ('create', 'edit', 'delete'):
            url = self.url(action, comment if action != 'create' else None)
            self.assertEqual(self.client.post(url).status_code, 302)
            ajax = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(ajax.status_code, 401)
            self.assertIn('login_url', ajax.json())
        self.assertEqual(CommunityComment.objects.count(), 1)

    def test_blank_and_overlong_comments_are_rejected_without_saving(self):
        self.client.force_login(self.customer)
        for content in ('', '   ', 'x' * 2001):
            with self.subTest(length=len(content)):
                response = self.client.post(self.url(), {'comment-content': content}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 400)
                self.assertContains(response, 'errorlist', status_code=400)
                self.assertFalse(CommunityComment.objects.exists())
        response = self.client.post(self.url(), {'comment-content': 'x' * 2000}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_comment_author_can_edit_and_delete(self):
        for user in (self.customer, self.merchant):
            with self.subTest(user=user.username):
                comment = CommunityComment.objects.create(post=self.post, author=user, content='Sebelum edit.')
                self.client.force_login(user)
                response = self.client.post(self.url('edit', comment), {f'edit-{comment.pk}-content': 'Setelah edit.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 200)
                comment.refresh_from_db()
                self.assertEqual(comment.content, 'Setelah edit.')
                response = self.client.post(self.url('delete', comment), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 200)
                self.assertFalse(CommunityComment.objects.filter(pk=comment.pk).exists())

    def test_invalid_edit_keeps_database_content_and_opens_form_with_error(self):
        comment = CommunityComment.objects.create(post=self.post, author=self.customer, content='Tetap tersimpan.')
        self.client.force_login(self.customer)
        response = self.client.post(self.url('edit', comment), {f'edit-{comment.pk}-content': ' '}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, f'id="edit-comment-{comment.pk}"', status_code=400)
        self.assertContains(response, 'data-open-on-load="true"', status_code=400)
        self.assertContains(response, 'aria-invalid="true"', status_code=400)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Tetap tersimpan.')

    def test_other_users_including_post_owner_cannot_manage_someone_elses_comment(self):
        comment = CommunityComment.objects.create(post=self.post, author=self.other, content='Milik orang lain.')
        for user in (self.customer, self.merchant):
            self.client.force_login(user)
            for action in ('edit', 'delete'):
                response = self.client.post(self.url(action, comment), {f'edit-{comment.pk}-content': 'Diubah.'})
                self.assertEqual(response.status_code, 404)
            detail = self.client.get(reverse('community:post_detail', args=[self.post.pk]))
            self.assertNotContains(detail, f'data-comment-dialog-open="edit-comment-{comment.pk}"')
            self.assertNotContains(detail, f'data-comment-dialog-open="delete-comment-{comment.pk}"')
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Milik orang lain.')

    def test_no_profile_account_is_rejected(self):
        user = get_user_model().objects.create_user(username='comment_no_profile')
        self.client.force_login(user)
        self.assertEqual(self.client.post(self.url(), {'comment-content': 'Tidak boleh.'}).status_code, 403)
        self.assertFalse(CommunityComment.objects.exists())

    def test_reviews_missing_posts_and_wrong_parent_are_rejected(self):
        self.client.force_login(self.customer)
        comment = CommunityComment.objects.create(post=self.post, author=self.customer, content='Tetap utuh.')
        self.assertEqual(self.client.post(self.url(post=self.review), {'comment-content': 'Review.'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('community:comment_create', args=[999999])).status_code, 404)
        for action in ('edit', 'delete'):
            self.assertEqual(self.client.post(self.url(action, comment, self.other_post)).status_code, 404)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Tetap utuh.')
        with self.assertRaises(ValidationError):
            CommunityComment(post=self.review, author=self.customer, content='Tidak valid.').full_clean()

    def test_comment_mutations_require_post_and_csrf(self):
        comment = CommunityComment.objects.create(post=self.post, author=self.customer, content='Aman.')
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        for action in ('create', 'edit', 'delete'):
            url = self.url(action, comment if action != 'create' else None)
            self.assertEqual(client.get(url).status_code, 405)
            self.assertEqual(client.post(url).status_code, 403)
        client.get(reverse('community:post_detail', args=[self.post.pk]))
        response = client.post(self.url(), {'comment-content': 'Dengan CSRF.'}, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CommunityComment.objects.count(), 2)

    def test_guest_sees_escaped_comments_in_order_and_merchant_badge(self):
        first = CommunityComment.objects.create(post=self.post, author=self.merchant, content='<script>alert(1)</script>\nBaris berikutnya.')
        second = CommunityComment.objects.create(post=self.post, author=self.customer, content='Komentar kedua.')
        response = self.client.get(reverse('community:post_detail', args=[self.post.pk]))
        self.assertEqual(response.context['comments'], [first, second])
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'food-hack-card__badge--merchant')
        self.assertContains(response, 'Penulis post')

    def test_non_ajax_redirect_preserves_feed_page(self):
        self.client.force_login(self.customer)
        feed = 'post_type=food_hack&sort=oldest&page=20'
        response = self.client.post(self.url(), {'comment-content': 'Halaman tetap.', 'feed': feed})
        self.assertEqual(response.status_code, 302)
        detail = self.client.get(response.url)
        self.assertEqual(detail.context['back_url'], reverse('community:home') + '?' + feed)

    def test_post_deletion_cascades_to_comments(self):
        CommunityComment.objects.create(post=self.post, author=self.merchant, content='Komentar.')
        self.post.delete()
        self.assertFalse(CommunityComment.objects.exists())

    def test_replies_and_nested_replies_stay_under_original_post(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Komentar induk.')
        self.client.force_login(self.merchant)
        reply_url = reverse('community:comment_reply', args=[self.post.pk, root.pk])
        response = self.client.post(reply_url, {f'reply-{root.pk}-content': 'Balasan merchant.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        reply = CommunityComment.objects.get(parent=root)
        self.assertEqual(reply.author, self.merchant)
        self.client.force_login(self.other)
        response = self.client.post(reverse('community:comment_reply', args=[self.post.pk, reply.pk]),
                                    {f'reply-{reply.pk}-content': 'Balasan lanjutan.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Membalas @comment_merchant')
        self.assertContains(response, 'community-comment__replies')
        self.assertEqual(response.context['root_comments'], [root])
        self.assertEqual(len(response.context['comments']), 3)
        self.assertEqual(CommunityPost.objects.count(), 3)
        feed = self.client.get(reverse('community:home'))
        self.assertNotContains(feed, 'Balasan merchant.')
        self.assertNotContains(feed, 'Balasan lanjutan.')

    def test_reply_cannot_target_comment_in_another_post(self):
        root = CommunityComment.objects.create(post=self.other_post, author=self.other, content='Di post lain.')
        self.client.force_login(self.customer)
        response = self.client.post(reverse('community:comment_reply', args=[self.post.pk, root.pk]), {f'reply-{root.pk}-content': 'Salah post.'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(CommunityComment.objects.count(), 1)
        with self.assertRaises(ValidationError):
            CommunityComment(post=self.post, author=self.customer, parent=root, content='Salah post.').full_clean()

    def test_blank_reply_keeps_reply_form_open_with_error(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        self.client.force_login(self.merchant)
        response = self.client.post(reverse('community:comment_reply', args=[self.post.pk, root.pk]),
                                    {f'reply-{root.pk}-content': ' '}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, f'id="reply-comment-{root.pk}"', status_code=400)
        self.assertContains(response, 'data-open-on-load="true"', status_code=400)
        self.assertContains(response, 'aria-invalid="true"', status_code=400)
        self.assertEqual(CommunityComment.objects.count(), 1)

    def test_comment_likes_toggle_independently_for_customer_and_merchant(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        reply = CommunityComment.objects.create(post=self.post, author=self.merchant, parent=root, content='Balasan.')
        for comment in (root, reply):
            url = reverse('community:comment_like', args=[self.post.pk, comment.pk])
            self.client.force_login(self.customer)
            self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 200)
            self.assertEqual(comment.likes.count(), 1)
            self.client.force_login(self.merchant)
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            rendered = next(item for item in response.context['comments'] if item.pk == comment.pk)
            self.assertEqual(rendered.like_count, 2)
            self.assertTrue(rendered.has_liked)
            self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(comment.likes.count(), 1)
            self.assertTrue(comment.likes.filter(pk=self.customer.pk).exists())

    def test_comment_like_uniqueness_and_persistence_after_refresh(self):
        comment = CommunityComment.objects.create(post=self.post, author=self.customer, content='Disukai.')
        comment.likes.add(self.merchant, self.merchant)
        self.assertEqual(comment.likes.count(), 1)
        self.client.force_login(self.merchant)
        response = self.client.get(reverse('community:post_detail', args=[self.post.pk]))
        self.assertContains(response, 'community-comment-like--active')
        self.assertEqual(response.context['comments'][0].like_count, 1)

    def test_reply_and_like_require_login_post_csrf_and_valid_role(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        urls = [reverse('community:comment_reply', args=[self.post.pk, root.pk]),
                reverse('community:comment_like', args=[self.post.pk, root.pk])]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 401)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        for url in urls:
            self.assertEqual(client.post(url).status_code, 403)
        user = get_user_model().objects.create_user(username='no_comment_role')
        self.client.force_login(user)
        for url in urls:
            self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(CommunityComment.objects.count(), 1)
        self.assertFalse(root.likes.exists())

    def test_comment_like_rejects_wrong_post_and_reviews(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        self.client.force_login(self.merchant)
        for post in (self.other_post, self.review):
            response = self.client.post(reverse('community:comment_like', args=[post.pk, root.pk]))
            self.assertEqual(response.status_code, 404)
        self.assertFalse(root.likes.exists())

    def test_deleting_parent_preserves_replies_by_other_users(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        reply = CommunityComment.objects.create(post=self.post, author=self.merchant, parent=root, content='Tetap ada.')
        reply.likes.add(self.other)
        self.client.force_login(self.customer)
        self.client.post(self.url('delete', root), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        reply.refresh_from_db()
        self.assertIsNone(reply.parent_id)
        self.assertEqual(reply.post, self.post)
        self.assertEqual(reply.likes.count(), 1)

    def test_feed_shows_comment_count_without_multiplying_post_likes(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        CommunityComment.objects.create(post=self.post, author=self.merchant, parent=root, content='Balasan.')
        self.post.upvotes.add(self.customer, self.merchant)
        self.client.force_login(self.customer)
        for headers in ({}, {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}):
            response = self.client.get(reverse('community:home'), {'page': 1}, **headers)
            post = next(post for post in response.context['posts'] if post.pk == self.post.pk)
            self.assertEqual(post.comment_count, 2)
            self.assertEqual(post.upvote_count, 2)
            self.assertContains(response, f'<span data-post-comment-count="{self.post.pk}">2</span>', html=True)
            self.assertContains(response, '#comment-form')
            self.assertNotContains(response, 'Balasan.</p>')

    def test_comment_count_updates_after_delete_and_new_reply(self):
        root = CommunityComment.objects.create(post=self.post, author=self.customer, content='Induk.')
        self.client.force_login(self.customer)
        response = self.client.post(reverse('community:comment_reply', args=[self.post.pk, root.pk]),
                                    {f'reply-{root.pk}-content': 'Balasan.'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'data-comment-count="2"')
        response = self.client.post(self.url('delete', root), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'data-comment-count="1"')


class CommunityPostTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_superuser(
            username='community_admin', password='test-password'
        )

    def make_post(self, **overrides):
        fields = dict(author=self.author, title='Simpan roti', content='Bekukan roti surplus.')
        fields.update(overrides)
        return CommunityPost(**fields)

    def test_food_hack_can_be_saved_and_read(self):
        post = self.make_post()
        post.full_clean()
        post.save()
        post.refresh_from_db()
        self.assertEqual(post.post_type, CommunityPost.PostType.FOOD_HACK)
        self.assertIsNone(post.rating)
        self.assertEqual(str(post), 'Simpan roti')
        self.assertEqual(post.author, self.author)
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)

    def test_invalid_post_type_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.make_post(post_type='invalid').full_clean()

    def test_blank_text_is_rejected(self):
        for field in ('title', 'content'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.make_post(**{field: '   '}).full_clean()

    def test_food_hack_cannot_have_rating(self):
        with self.assertRaises(ValidationError):
            self.make_post(rating=3).full_clean()

    def test_review_rating_range(self):
        order = completed_order(self.author)
        for rating in (None, 0, 6):
            with self.subTest(rating=rating), self.assertRaises(ValidationError):
                self.make_post(post_type='review', rating=rating, related_order=order).full_clean()
        for rating in (1, 5):
            self.make_post(post_type='review', rating=rating, related_order=order).full_clean()

    def test_admin_can_create_and_read_food_hack(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('admin:community_communitypost_add'), {
            'author': self.author.pk,
            'post_type': 'food_hack',
            'title': 'Simpan roti',
            'content': 'Bekukan roti surplus.',
            'rating': '',
            '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        post = CommunityPost.objects.get(title='Simpan roti')
        response = self.client.get(reverse('admin:community_communitypost_change', args=[post.pk]))
        self.assertContains(response, 'Simpan roti')
        response = self.client.get(reverse('admin:community_communitypost_changelist'))
        self.assertContains(response, 'Simpan roti')

    def test_admin_defers_review_creation(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('admin:community_communitypost_add'), {
            'author': self.author.pk, 'post_type': 'review',
            'title': 'Review', 'content': 'Enak', 'rating': 5,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CommunityPost.objects.exists())


class ReviewPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = get_user_model().objects.create_user(username='review_page_customer')
        cls.other = get_user_model().objects.create_user(username='review_page_other')
        cls.merchant = get_user_model().objects.create_user(username='review_page_merchant')
        cls.no_profile = get_user_model().objects.create_user(username='review_page_no_profile')
        for user, role in (
            (cls.customer, UserProfile.Role.CUSTOMER),
            (cls.other, UserProfile.Role.CUSTOMER),
            (cls.merchant, UserProfile.Role.MERCHANT),
        ):
            UserProfile.objects.create(user=user, role=role)
        cls.completed = completed_order(cls.customer, cls.merchant)

    def setUp(self):
        self.client.force_login(self.customer)
        self.url = reverse('community:review_create')

    def payload(self, **changes):
        values = {'rating': '4', 'content': 'Makanannya enak dan porsinya cukup.',
                  'related_order': str(self.completed.pk)}
        values.update(changes)
        return values


    def test_form_is_available_by_url_without_feed_button(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'type="radio"', count=5)
        self.assertContains(response, 'Pesanan yang diulas')
        self.assertNotContains(response, 'multipart/form-data')
        self.assertNotContains(response, 'name="title"')
        self.assertNotContains(response, 'anonym')
        self.assertEqual(set(response.context['form'].fields), {'related_order', 'rating', 'content'})
        self.assertNotContains(self.client.get(reverse('community:home')), self.url)

    def test_review_is_saved_with_server_owned_fields_and_shown_in_feed(self):
        response = self.client.post(self.url, self.payload(
            author=self.other.pk, title='Judul palsu', post_type='food_hack', verified='true',
        ))
        post = CommunityPost.objects.get()
        self.assertEqual(post.author, self.customer)
        self.assertEqual(post.post_type, 'review')
        self.assertEqual(post.title, f'Review {self.completed.food_name}')
        self.assertEqual(post.related_order, self.completed)
        self.assertEqual(post.rating, 4)
        self.assertRedirects(response, reverse('community:review_detail', args=[post.pk]))
        result = self.client.get(response.url)
        self.assertContains(result, 'Pembelian terverifikasi')
        self.assertContains(result, post.content)
        self.assertNotContains(result, 'Verified Purchase')
        feed = self.client.get(reverse('community:home'))
        self.assertContains(feed, post.content)
        self.assertContains(feed, response.url + '?feed=')
        self.assertContains(feed, 'Pembelian terverifikasi')

    def test_rating_and_description_validation(self):
        invalid = [self.payload(rating=value) for value in ('', '0', '6', 'four')]
        invalid += [self.payload(content='   ')]
        for payload in invalid:
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(CommunityPost.objects.exists())

    def test_guest_uses_shared_login_and_roles_are_enforced(self):
        self.client.logout()
        for method in (self.client.get, self.client.post):
            response = method(self.url, self.payload())
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
        for user in (self.merchant, self.no_profile):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url, self.payload()).status_code, 403)

    def test_review_is_public_but_food_hacks_and_missing_ids_are_rejected(self):
        response = self.client.post(self.url, self.payload())
        url = response.url
        self.client.force_login(self.other)
        self.assertContains(self.client.get(url), 'Pembelian terverifikasi')
        self.client.force_login(self.merchant)
        self.assertContains(self.client.get(url), 'Pembelian terverifikasi')
        self.client.logout()
        self.assertContains(self.client.get(url), 'Pembelian terverifikasi')
        self.client.force_login(self.customer)
        food_hack = CommunityPost.objects.create(author=self.customer, title='Tips', content='Konten.')
        self.assertEqual(self.client.get(reverse('community:review_detail', args=[food_hack.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('community:review_detail', args=[99999])).status_code, 404)


    def test_review_search_ajax_and_detail_back_link_preserve_feed(self):
        response = self.client.post(self.url, self.payload(content='Croissant renyah sekali.'))
        post = CommunityPost.objects.get()
        feed = self.client.get(reverse('community:home'), {
            'post_type': 'review', 'q': 'croissant', 'sort': 'oldest',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(list(feed.context['posts']), [post])
        self.assertTemplateUsed(feed, 'community/components/review_card.html')
        self.assertNotContains(feed, 'data-upvote-form')
        query = 'post_type=review&q=croissant&sort=oldest&page=3'
        detail = self.client.get(response.url, {'feed': query})
        self.assertEqual(detail.context['back_url'], reverse('community:home') + '?' + query)

    def test_category_sort_options_and_invalid_sort_fallback(self):
        for category, expected in (
            ('all', ['newest', 'oldest']),
            ('food_hack', ['newest', 'oldest', 'likes']),
            ('review', ['newest', 'oldest', 'rating_highest', 'rating_lowest']),
        ):
            for ajax in (False, True):
                headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'} if ajax else {}
                response = self.client.get(reverse('community:home'), {'post_type': category}, **headers)
                self.assertEqual([value for value, label in response.context['sort_options']], expected)
                self.assertContains(response, 'id="community-sort-options"')
            for sort in ('likes', 'rating_highest', 'rating_lowest'):
                response = self.client.get(reverse('community:home'), {'post_type': category, 'sort': sort})
                self.assertEqual(response.context['selected_sort'], sort if sort in expected else 'newest')

    def test_review_rating_sort_and_back_links_are_stable(self):
        posts = [CommunityPost.objects.create(
            author=self.customer, title=f'Review {number}', content='Ulasan.', post_type='review', rating=rating,
        ) for number, rating in enumerate((1, 5, 5))]
        for sort, expected in (
            ('rating_highest', [posts[2], posts[1], posts[0]]),
            ('rating_lowest', [posts[0], posts[2], posts[1]]),
        ):
            response = self.client.get(reverse('community:home'), {'post_type': 'review', 'sort': sort, 'q': 'Ulasan'})
            self.assertEqual(list(response.context['posts']), expected)
            self.assertIn('sort=' + sort, response.context['filter_query'])
            self.assertNotIn('sort=', response.context['all_posts_query'])
            self.assertNotIn('sort=', response.context['food_hacks_query'])
            self.assertIn('q=Ulasan', response.context['all_posts_query'])

    def test_review_hides_heart_and_ignores_liked_filter_even_for_guest(self):
        self.client.post(self.url, self.payload())
        self.client.logout()
        response = self.client.get(reverse('community:home'), {'post_type': 'review', 'liked': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['liked_only'])
        self.assertEqual(len(response.context['posts']), 1)
        self.assertNotIn('liked=', response.context['filter_query'])
        self.assertRegex(response.content.decode(), r'class="community-sort community-food-hack-filter"[^>]* hidden')
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack', 'sort': 'likes'})
        self.assertNotRegex(response.content.decode(), r'class="community-sort community-food-hack-filter"[^>]* hidden')
        self.assertNotIn('liked=', response.context['reviews_query'])
        self.assertNotIn('sort=', response.context['reviews_query'])


    def test_rating_filter_combines_with_search_sort_and_pagination(self):
        CommunityPost.objects.bulk_create([
            CommunityPost(author=self.customer, post_type='review', title='Pesanan', rating=5, content='Roti enak.')
            for _ in range(12)
        ])
        CommunityPost.objects.create(author=self.customer, post_type='review', title='Pesanan', rating=1, content='Roti kering.')
        CommunityPost.objects.create(author=self.customer, title='Roti', content='Tips roti.')
        for ajax in (False, True):
            headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'} if ajax else {}
            response = self.client.get(reverse('community:home'), {
                'post_type': 'review', 'rating': '5', 'q': 'roti', 'sort': 'oldest', 'page': 2,
            }, **headers)
            self.assertEqual(response.context['selected_rating'], '5')
            self.assertEqual(response.context['page_obj'].paginator.count, 12)
            self.assertEqual(len(response.context['posts']), 2)
            self.assertTrue(all(post.rating == 5 for post in response.context['posts']))
            self.assertIn('rating=5', response.context['clear_query'])
            self.assertIn('rating=5', response.context['filter_query'])
            self.assertNotIn('rating=', response.context['all_posts_query'])
            self.assertNotIn('rating=', response.context['food_hacks_query'])
            self.assertContains(response, 'rating=5&amp;q=roti&amp;page=1')

    def test_filters_are_ignored_outside_their_own_tab_and_invalid_ratings_are_safe(self):
        for category in ('all', 'food_hack', 'review'):
            for value in ('all', '0', '6', 'invalid', 'visuals'):
                response = self.client.get(reverse('community:home'), {'post_type': category, 'rating': value})
                self.assertEqual(response.context['selected_rating'], 'all')
                self.assertNotIn('rating=', response.context['filter_query'])
        self.client.logout()
        for category in ('all', 'review'):
            response = self.client.get(reverse('community:home'), {'post_type': category, 'liked': '1', 'rating': '5'})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['liked_only'])
            self.assertRegex(response.content.decode(), r'class="community-sort community-food-hack-filter"[^>]* hidden')
            self.assertNotIn('liked=', response.context['filter_query'])


    def test_search_uses_titles_and_content_within_each_category(self):
        tip = CommunityPost.objects.create(author=self.customer, title='KataUnik', content='Simpan makanan.')
        review_title = CommunityPost.objects.create(author=self.customer, post_type='review', title='KataUnik', content='Porsi cukup.', rating=5)
        review_content = CommunityPost.objects.create(author=self.customer, post_type='review', title='Pesanan', content='KataUnik terasa enak.', rating=4)
        for category, expected in (
            ('all', [review_content, review_title, tip]), ('food_hack', [tip]), ('review', [review_content, review_title]),
        ):
            response = self.client.get(reverse('community:home'), {'post_type': category, 'q': 'kataunik'})
            self.assertEqual(list(response.context['posts']), expected)
            if category == 'review':
                self.assertContains(response, 'Search Reviews...')

    def test_controls_follow_tab_search_filter_sort_order_and_requested_labels(self):
        response = self.client.get(reverse('community:home'), {'post_type': 'food_hack'})
        html = response.content.decode()
        positions = [html.index(marker) for marker in (
            'class="community-tabs"', 'id="community-search-form"', 'id="community-liked"', 'id="community-sort"',
        )]
        self.assertEqual(positions, sorted(positions))
        self.assertContains(response, 'All Food Hacks')
        self.assertContains(response, 'Liked by Me')
        self.assertNotContains(response, 'community-liked-filter')
        for category, placeholder in (
            ('all', 'Search Community...'), ('food_hack', 'Search Food Hacks...'), ('review', 'Search Reviews...'),
        ):
            response = self.client.get(reverse('community:home'), {'post_type': category})
            self.assertContains(response, f'placeholder="{placeholder}"')
        self.assertEqual(response.context['rating_options'], ['5', '4', '3', '2', '1'])

    def test_switching_tab_links_resets_shared_sort_to_newest_too(self):
        for category, other_keys in (
            ('all', ('food_hacks_query', 'reviews_query')),
            ('food_hack', ('all_posts_query', 'reviews_query')),
            ('review', ('all_posts_query', 'food_hacks_query')),
        ):
            response = self.client.get(reverse('community:home'), {
                'post_type': category, 'sort': 'oldest', 'rating': '5', 'q': 'roti',
            })
            for key in other_keys:
                self.assertNotIn('sort=', response.context[key])
                self.assertNotIn('rating=', response.context[key])
                self.assertNotIn('liked=', response.context[key])
                self.assertIn('q=roti', response.context[key])

    def test_liked_food_hack_tab_links_drop_likes_for_all_and_reviews(self):
        response = self.client.get(reverse('community:home'), {
            'post_type': 'food_hack', 'liked': '1', 'sort': 'likes', 'q': 'roti',
        })
        self.assertIn('liked=1', response.context['food_hacks_query'])
        for key in ('all_posts_query', 'reviews_query'):
            self.assertNotIn('liked=', response.context[key])
            self.assertNotIn('sort=', response.context[key])
            self.assertIn('q=roti', response.context[key])

    def test_csrf_methods_and_output_escaping(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        self.assertEqual(client.post(self.url, self.payload()).status_code, 403)
        self.assertEqual(self.client.put(self.url).status_code, 405)
        response = self.client.post(self.url, self.payload(content='<script>alert(1)</script>'))
        result = self.client.get(response.url)
        self.assertContains(result, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(result, '<script>alert(1)</script>')
        self.assertEqual(self.client.post(response.url).status_code, 405)

    def test_order_selector_only_offers_unreviewed_completed_orders_owned_by_customer(self):
        foreign = completed_order(self.other, self.merchant)
        pending = completed_order(self.customer, self.merchant, status='pending', completed_at=None)
        response = self.client.get(self.url, {'order': self.completed.pk})
        field = response.context['form'].fields['related_order']
        self.assertEqual(list(field.queryset), [self.completed])
        self.assertEqual(response.context['form'].initial['related_order'], self.completed.pk)
        self.assertNotContains(response, str(foreign.pk))
        self.assertNotContains(response, str(pending.pk))

    def test_foreign_missing_malformed_or_uncompleted_order_cannot_be_reviewed(self):
        foreign = completed_order(self.other, self.merchant)
        invalid_ids = [foreign.pk, uuid.uuid4(), 'invalid-id', '']
        for status in ('pending', 'ready_to_pickup', 'cancelled'):
            invalid_ids.append(completed_order(self.customer, self.merchant, status=status, completed_at=None).pk)
        for order_id in invalid_ids:
            with self.subTest(order_id=order_id):
                response = self.client.post(self.url, self.payload(related_order=str(order_id)))
                self.assertTrue(response.context['form'].errors.get('related_order'))
                if order_id:
                    self.assertEqual(self.client.get(self.url, {'order': order_id}).status_code, 404)
        self.assertFalse(CommunityPost.objects.exists())

    def test_completed_order_can_only_be_reviewed_once_even_after_repeated_post(self):
        response = self.client.post(self.url, self.payload())
        repeat = self.client.post(self.url, self.payload())
        self.assertTrue(repeat.context['form'].errors.get('related_order'))
        self.assertEqual(CommunityPost.objects.count(), 1)
        self.assertRedirects(self.client.get(self.url, {'order': self.completed.pk}), response.url)
        self.assertFalse(self.client.get(self.url).context['has_eligible_orders'])

    def test_duplicate_review_is_also_rejected_by_database(self):
        from django.db import IntegrityError, transaction
        self.client.post(self.url, self.payload())
        with self.assertRaises(IntegrityError), transaction.atomic():
            CommunityPost.objects.create(author=self.customer, related_order=self.completed,
                                         post_type='review', title='Duplikat', content='Duplikat', rating=5)

    def test_model_validates_review_order_ownership_status_and_food_hack_relation(self):
        for owner, order in ((self.other, self.completed),
                             (self.customer, completed_order(self.customer, self.merchant, status='pending', completed_at=None)),
                             (self.customer, None)):
            with self.assertRaises(ValidationError):
                CommunityPost(author=owner, related_order=order, post_type='review',
                              title='Review', content='Enak', rating=5).full_clean()
        with self.assertRaises(ValidationError):
            CommunityPost(author=self.customer, related_order=self.completed,
                          title='Tips', content='Tips.').full_clean()

    def test_review_submission_is_asynchronous_with_validated_json_errors(self):
        headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        invalid = self.client.post(self.url, self.payload(related_order=str(uuid.uuid4())), **headers)
        self.assertEqual(invalid.status_code, 400)
        self.assertIn('related_order', invalid.json()['errors'])
        response = self.client.post(self.url, self.payload(), **headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['detail_url'], reverse('community:review_detail', args=[CommunityPost.objects.get().pk]))
        repeated = self.client.post(self.url, self.payload(), **headers)
        self.assertEqual(repeated.status_code, 400)
        self.assertEqual(CommunityPost.objects.count(), 1)

    def test_order_cards_link_completed_orders_to_review_then_existing_review(self):
        pending = completed_order(self.customer, self.merchant, status='pending', completed_at=None)
        expected = self.url + '?order=' + str(self.completed.pk)
        self.assertContains(self.client.get(reverse('order:list')), expected)
        self.assertNotContains(self.client.get(reverse('order:list')), self.url + '?order=' + str(pending.pk))
        response = self.client.post(self.url, self.payload())
        cards = self.client.get(reverse('order:orders_api')).json()['html']
        self.assertIn(response.url, cards)
        self.assertIn('Lihat Review', cards)
        self.assertNotIn(expected, cards)
        self.client.force_login(self.merchant)
        self.assertNotContains(self.client.get(reverse('order:list')), 'Tulis Review')

    def test_public_verified_review_does_not_expose_private_transaction_code(self):
        response = self.client.post(self.url, self.payload())
        self.client.logout()
        for url in (response.url, reverse('community:home')):
            page = self.client.get(url)
            self.assertContains(page, 'Pembelian terverifikasi')
            self.assertContains(page, self.merchant.username)
            self.assertNotContains(page, self.completed.pickup_code)
            self.assertNotContains(page, str(self.completed.reservation_key))

    def test_store_rating_counts_only_verified_reviews_for_its_owner(self):
        from merchant_store.models import MerchantStore
        from merchant_store.ratings import get_rating, get_rating_map
        store = MerchantStore.objects.create(owner=self.merchant, name='Toko Roti',
                    address='Depok', phone='081234567890', opening_time=time(8), closing_time=time(22))
        self.client.post(self.url, self.payload(rating=4))
        second = completed_order(self.other, self.merchant)
        CommunityPost.objects.create(author=self.other, related_order=second, post_type='review',
                                     title='Review lain', content='Enak.', rating=5)
        CommunityPost.objects.create(author=self.customer, post_type='review',
                                     title='Demo lama', content='Demo.', rating=1)
        pending = completed_order(self.customer, self.merchant, status='pending', completed_at=None)
        CommunityPost.objects.create(author=self.customer, related_order=pending, post_type='review',
                                     title='Tidak valid', content='Tidak valid.', rating=1)
        foreign = completed_order(self.other, self.merchant)
        CommunityPost.objects.create(author=self.customer, related_order=foreign, post_type='review',
                                     title='Bukan pemilik', content='Tidak valid.', rating=1)
        self.assertEqual(get_rating(store.pk), (4.5, 2))
        self.assertEqual(get_rating_map([]), {})
        self.assertEqual(get_rating(99999), (None, 0))
        self.assertEqual(self.client.get(reverse('merchant_store:detail', args=[store.pk])).status_code, 200)
