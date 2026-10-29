from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CommunityPost(models.Model):
    class PostType(models.TextChoices):
        FOOD_HACK = 'food_hack', 'Food Hack'
        REVIEW = 'review', 'Review'

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
    )
    post_type = models.CharField(
        max_length=10, choices=PostType.choices, default=PostType.FOOD_HACK
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='upvoted_community_posts',
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    related_order = models.ForeignKey(
        'order.Order', on_delete=models.PROTECT, null=True, blank=True,
        related_name='community_posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        # Satu pesanan hanya boleh diulas sekali.
        constraints = [
            models.UniqueConstraint(
                fields=['related_order'], condition=models.Q(post_type='review'),
                name='community_unique_order_review',
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_verified_purchase(self):
        # Pesanan harus selesai dan milik penulis review.
        if self.post_type != self.PostType.REVIEW:
            return False
        if not self.related_order_id:
            return False

        order = self.related_order
        return order.status == 'completed' and order.customer_id == self.author_id

    def clean(self):
        super().clean()
        errors = {}

        # Tolak judul atau isi yang hanya berupa spasi.
        if not self.title or not self.title.strip():
            errors['title'] = 'Field ini tidak boleh kosong.'
        if not self.content or not self.content.strip():
            errors['content'] = 'Field ini tidak boleh kosong.'

        # Rating wajib untuk Review, tidak berlaku untuk Food Hack.
        if self.post_type == self.PostType.FOOD_HACK and self.rating is not None:
            errors['rating'] = 'Food Hack tidak boleh memiliki rating.'
        elif self.post_type == self.PostType.REVIEW and self.rating is None:
            errors['rating'] = 'Review wajib memiliki rating.'

        # Periksa hubungan review dengan pesanan.
        if self.post_type == self.PostType.REVIEW and not self.is_verified_purchase:
            errors['related_order'] = 'Review harus memakai pesanan Completed milik penulis.'
        elif self.post_type != self.PostType.REVIEW and self.related_order_id:
            errors['related_order'] = 'Food Hack tidak boleh dihubungkan ke pesanan.'

        if errors:
            raise ValidationError(errors)


class MerchantReviewReply(models.Model):
    review = models.OneToOneField(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='merchant_reply',
    )
    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_replies',
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        errors = {}
        if not self.content or not self.content.strip():
            errors['content'] = 'Balasan tidak boleh kosong.'

        # Hanya Merchant pemilik pesanan yang boleh membalas.
        if self.review_id and (
            not self.review.is_verified_purchase
            or self.review.related_order.surprise_bag.merchant_id != self.merchant_id
        ):
            errors['review'] = 'Balasan hanya untuk Review terverifikasi dari pesanan Merchant ini.'

        if errors:
            raise ValidationError(errors)


class CommunityComment(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    # parent kosong untuk komentar utama.
    # Balasan tetap ada jika komentar induknya dihapus.
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_comments',
    )
    content = models.TextField(max_length=2000)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='liked_community_comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'pk']

    def __str__(self):
        return f'{self.author} — {self.content[:50]}'

    def clean(self):
        super().clean()
        errors = {}
        if not self.content or not self.content.strip():
            errors['content'] = 'Komentar tidak boleh kosong.'

        # Komentar hanya tersedia untuk Food Hack.
        if self.post_id and self.post.post_type != CommunityPost.PostType.FOOD_HACK:
            errors['post'] = 'Komentar hanya tersedia untuk Food Hack.'

        # Induk harus berada di postingan yang sama dan bukan dirinya sendiri.
        if self.parent_id:
            if self.parent.post_id != self.post_id:
                errors['parent'] = 'Balasan harus berada di postingan yang sama.'
            elif self.parent_id == self.pk:
                errors['parent'] = 'Komentar tidak dapat membalas dirinya sendiri.'

        if errors:
            raise ValidationError(errors)
