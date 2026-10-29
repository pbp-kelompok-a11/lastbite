from decimal import Decimal

from django.db.models import DecimalField, F, Sum
from django.shortcuts import render
from django.utils import timezone

from eco_impact.models import ImpactLog
from surprise_bag.models import SurpriseBag

# asumsi yang sama dengan ImpactLog.carbon_prevented_kg di modul Eco Impact
AVG_FOOD_WEIGHT_KG = Decimal('0.3')
EMISSION_FACTOR = Decimal('2.5')


def _community_impact():
    """Ringkasan dampak seluruh pengguna bulan ini, untuk strip hijau di landing page."""
    month_start = timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    totals = ImpactLog.objects.filter(created_at__gte=month_start).aggregate(
        portions=Sum('quantity'),
        money=Sum(
            (F('original_price') - F('discounted_price')) * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )
    food_kg = (totals['portions'] or 0) * AVG_FOOD_WEIGHT_KG
    money = totals['money'] or Decimal('0')
    return {
        'food_kg': food_kg,
        'carbon_kg': food_kg * EMISSION_FACTOR,
        'money_saved': money,
        'money_millions': money / 1_000_000,
    }


def home(request):
    """Landing page / home view."""
    # 3 surprise bag aktif dengan stok paling sedikit -> bagian "Hampir habis"
    featured_bags = (
        SurpriseBag.objects.filter(is_active=True, stock__gt=0)
        .select_related('merchant')
        .order_by('stock', '-created_at')[:3]
    )
    context = {
        'featured_bags': featured_bags,
        'impact': _community_impact(),
        # total porsi yang pernah diselamatkan, untuk kartu kecil di foto hero
        'total_portions': ImpactLog.objects.aggregate(total=Sum('quantity'))['total'] or 0,
    }
    return render(request, 'main/home.html', context)
