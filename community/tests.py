from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CommunityPost


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
