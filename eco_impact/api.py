from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import is_customer

from .models import ImpactLog


class ImpactLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpactLog
        fields = (
            'id', 'food_name', 'quantity', 'source', 'notes',
            'money_saved', 'carbon_prevented_kg', 'created_at',
        )


class ImpactLogList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImpactLogSerializer

    def get_queryset(self):
        if not is_customer(self.request.user):
            raise PermissionDenied('Jurnal dampak hanya tersedia untuk Customer.')
        return ImpactLog.objects.filter(user=self.request.user).order_by('-created_at', '-pk')
