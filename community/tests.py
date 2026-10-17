from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CommunityPost
from accounts.models import UserProfile


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

    def test_guest_sees_food_hacks_newest_first_and_not_reviews(self):
        older = self.create_post(title='Tips roti lama')
        CommunityPost.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(days=1))
        newer = self.create_post(title='Tips sayur baru')
        self.create_post(title='Review tidak masuk feed ini', post_type='review', rating=5)
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertEqual(list(response.context['posts']), [newer, older])
        self.assertContains(response, 'food_hack_writer')
        self.assertContains(response, 'Bekukan roti dalam wadah tertutup.')
        self.assertNotContains(response, 'Review tidak masuk feed ini')

    def test_empty_feed(self):
        response = self.client.get(reverse('community:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Belum ada Food Hack')
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
                response = self.client.get(reverse('community:home'), {'q': query})
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

    def test_supported_tabs_do_not_expose_unverified_reviews(self):
        for post_type in ('all', 'food_hack'):
            with self.subTest(post_type=post_type):
                response = self.client.get(reverse('community:home'), {'post_type': post_type})
                self.assertEqual(response.context['selected_post_type'], post_type)
                self.assertEqual(set(response.context['posts']), {self.bread, self.vegetable})
                self.assertNotContains(response, self.review.title)
                self.assertContains(response, 'class="community-tab community-tab--active"', count=1)
                label = 'All Posts' if post_type == 'all' else 'Food Hacks'
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
        self.assertEqual(set(response.context['posts']), {self.bread, self.vegetable})

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
                self.assertTemplateUsed(response, 'community/post_detail.html')
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
        for page, expected_count in ((1, 10), (2, 10), (3, 3)):
            response = self.client.get(reverse('community:home'), {'page': page})
            posts = list(response.context['posts'])
            self.assertEqual(len(posts), expected_count)
            self.assertEqual(response.context['page_obj'].paginator.count, 23)
            actual.extend(post.pk for post in posts)
        expected = list(CommunityPost.objects.filter(post_type='food_hack').values_list('pk', flat=True))
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
        self.assertEqual(len(response.context['posts']), 3)
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
            for number in range(977)
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
                response = self.client.get(reverse('community:home'), {'sort': sort})
                self.assertEqual(list(response.context['posts']), expected)

    def test_equal_dates_and_likes_have_stable_order(self):
        CommunityPost.objects.update(created_at=timezone.now())
        self.newer.upvotes.add(self.other)
        response = self.client.get(reverse('community:home'), {'sort': 'likes'})
        self.assertEqual(list(response.context['posts']), [self.popular, self.newer, self.older])

    def test_liked_filter_only_uses_current_user_and_keeps_total_counts(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('community:home'), {'liked': '1', 'sort': 'likes'})
        self.assertEqual(list(response.context['posts']), [self.popular, self.older])
        self.assertEqual(response.context['posts'][0].upvote_count, 2)
        self.client.force_login(self.other)
        response = self.client.get(reverse('community:home'), {'liked': '1'})
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
        response = self.client.get(reverse('community:home'), {'liked': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
        response = self.client.get(reverse('community:home'), {'liked': '1'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 401)
        self.assertIn('login_url', response.json())

    def test_empty_liked_state_after_unlike_and_toggle_off(self):
        self.client.force_login(self.other)
        self.client.post(reverse('community:post_upvote', args=[self.popular.pk]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.get(reverse('community:home'), {'liked': '1'})
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
        liked_feed = self.client.get(reverse('community:home'), {'liked': '1'})
        self.assertEqual(list(liked_feed.context['posts']), [self.post])
        self.assertContains(liked_feed, 'aria-pressed="true"')
        self.assertFalse(self.vote().json()['has_upvoted'])
        self.assertFalse(self.post.upvotes.exists())
        self.assertQuerySetEqual(self.client.get(reverse('community:home'), {'liked': '1'}).context['posts'], [])

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
        for rating in (None, 0, 6):
            with self.subTest(rating=rating), self.assertRaises(ValidationError):
                self.make_post(post_type='review', rating=rating).full_clean()
        for rating in (1, 5):
            self.make_post(post_type='review', rating=rating).full_clean()

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
