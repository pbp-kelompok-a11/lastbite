from django.shortcuts import render
from surprise_bag.models import SurpriseBag


def home(request):
    """Landing page / home view."""
    # 4 surprise bag terbaru yang masih aktif dan ada stoknya
    featured_bags = (
        SurpriseBag.objects.filter(is_active=True, stock__gt=0)
        .select_related('merchant')[:4]
    )
    context = {
        'featured_bags': featured_bags,
    }
    return render(request, 'main/home.html', context)
