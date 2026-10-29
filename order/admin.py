from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'food_name', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'pickup_date']
    search_fields = ['food_name', 'customer__username']
    readonly_fields = [field.name for field in Order._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
