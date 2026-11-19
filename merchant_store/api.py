from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import MerchantStore
from .views import _directory_stores


class MerchantStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantStore
        fields = (
            'id', 'name', 'description', 'address', 'phone', 'business_email',
            'opening_time', 'closing_time', 'photo', 'latitude', 'longitude',
        )


class MerchantStoreList(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MerchantStoreSerializer

    def get_queryset(self):
        return _directory_stores().filter(is_active=True).order_by('name', 'pk')
