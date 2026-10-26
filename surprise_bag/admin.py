from django.contrib import admin
from .models import SurpriseBag


@admin.register(SurpriseBag)
class SurpriseBagAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'category', 'original_price', 'discounted_price',
                    'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'merchant__username')
    list_editable = ('stock', 'is_active')
