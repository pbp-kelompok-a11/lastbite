from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import SurpriseBag


class SurpriseBagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurpriseBag
        fields = (
            'id', 'name', 'description', 'category', 'original_price',
            'discounted_price', 'stock', 'pickup_start', 'pickup_end',
            'merchant_name', 'image_src',
        )


class SurpriseBagList(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = SurpriseBagSerializer
    queryset = (
        SurpriseBag.objects.filter(is_active=True, stock__gt=0)
        .select_related('merchant__merchant_store')
        .order_by('-created_at', 'pk')
    )
