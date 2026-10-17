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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        for field in ('title', 'content'):
            value = getattr(self, field)
            if not value or not value.strip():
                errors[field] = 'Field ini tidak boleh kosong.'
        if self.post_type == self.PostType.FOOD_HACK and self.rating is not None:
            errors['rating'] = 'Food Hack tidak boleh memiliki rating.'
        elif self.post_type == self.PostType.REVIEW and self.rating is None:
            errors['rating'] = 'Review wajib memiliki rating.'
        if errors:
            raise ValidationError(errors)
