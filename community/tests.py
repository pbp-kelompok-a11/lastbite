from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import CommunityPost


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
