from django.db.models import Count, F
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from order.models import Order

from .models import CommunityPost


class FoodHackSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.get_username', read_only=True)
    upvote_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CommunityPost
        fields = ('id', 'title', 'content', 'author', 'upvote_count', 'created_at')


class VerifiedReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.get_username', read_only=True)
    merchant_name = serializers.CharField(
        source='related_order.surprise_bag.merchant_name', read_only=True,
    )

    class Meta:
        model = CommunityPost
        fields = ('id', 'title', 'content', 'author', 'merchant_name', 'rating', 'created_at')


class FoodHackList(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FoodHackSerializer
    queryset = (
        CommunityPost.objects.filter(post_type=CommunityPost.PostType.FOOD_HACK)
        .select_related('author')
        .annotate(upvote_count=Count('upvotes'))
        .order_by('-created_at', '-pk')
    )


class VerifiedReviewList(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifiedReviewSerializer
    queryset = (
        CommunityPost.objects.filter(
            post_type=CommunityPost.PostType.REVIEW,
            related_order__status=Order.Status.COMPLETED,
            related_order__customer_id=F('author_id'),
        )
        .select_related('author', 'related_order__surprise_bag__merchant__merchant_store')
        .order_by('-created_at', '-pk')
    )
