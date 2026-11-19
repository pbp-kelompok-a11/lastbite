from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .views import _visible_orders


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            'id', 'surprise_bag', 'food_name', 'quantity', 'discounted_price',
            'total_price', 'status', 'pickup_date', 'pickup_start', 'pickup_end',
            'created_at', 'completed_at',
        )


class OrderList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        # Terapkan aturan akses yang sama dengan daftar pesanan di web.
        return _visible_orders(self.request.user).order_by('-created_at', '-pk')
