from django.contrib import admin

from .models import MerchantStore, StoreWishlist


@admin.register(MerchantStore)
class MerchantStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address', 'is_active', 'latitude', 'longitude')
    list_filter = ('is_active',)
    search_fields = ('name', 'address', 'owner__username')
    list_select_related = ('owner',)


@admin.register(StoreWishlist)
class StoreWishlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'store', 'created_at')
    search_fields = ('customer__username', 'store__name')
    list_select_related = ('customer', 'store')
