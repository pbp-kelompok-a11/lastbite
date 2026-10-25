from django.contrib import admin
from .models import ImpactLog


@admin.register(ImpactLog)
class ImpactLogAdmin(admin.ModelAdmin):
    # kolom yang langsung keliatan di list admin
    list_display = ('user', 'food_name', 'quantity', 'money_saved', 'carbon_prevented_kg', 'source', 'created_at')

    # filter samping kanan di admin
    list_filter = ('source', 'created_at')
    search_fields = ('user__username', 'food_name')

    # field kalkulasi jangan bisa diedit manual, biar konsisten
    readonly_fields = ('money_saved', 'carbon_prevented_kg', 'created_at', 'updated_at')