import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.views.decorators.http import require_POST

from .forms import SurpriseBagForm, SurpriseBagUpdateForm
from .models import SurpriseBag


def is_merchant(user):
    # sementara role merchant ditandai lewat Group "Merchant";
    # nanti bisa diganti cek ke MerchantStore setelah modul itu di-merge
    return user.is_authenticated and user.groups.filter(name='Merchant').exists()


def merchant_required(view_func):
    """Hanya user login dengan role Merchant yang boleh lanjut."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_merchant(request.user):
            return HttpResponseForbidden('Halaman ini khusus untuk Merchant.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _parse_price(value):
    # input harga dari query string bisa kosong / ngawur, jadi diamankan dulu
    try:
        price = Decimal(value)
    except (InvalidOperation, TypeError):
        return None
    return price if price.is_finite() else None


def _get_visible_bag(request, pk):
    # bag nonaktif hanya boleh dilihat pemiliknya
    bag = get_object_or_404(SurpriseBag.objects.select_related('merchant'), pk=pk)
    if not bag.is_active and bag.merchant != request.user:
        raise Http404
    return bag


# --- Halaman publik (Guest & Customer) ---

def catalog(request):
    # halaman katalog — kartu-kartunya diisi via AJAX dari catalog_api
    return render(request, 'surprise_bag/catalog.html', {
        'categories': SurpriseBag.CATEGORY_CHOICES,
        'is_merchant': is_merchant(request.user),
    })


def bag_detail(request, pk):
    bag = _get_visible_bag(request, pk)
    return render(request, 'surprise_bag/detail.html', {
        'bag': bag,
        'is_owner': bag.merchant == request.user,
        'login_url': f'{resolve_url(settings.LOGIN_URL)}?next={request.path}',
    })


# --- Halaman Merchant (CRUD) ---

@merchant_required
def my_bags(request):
    bags = request.user.surprise_bags.all()
    return render(request, 'surprise_bag/my_bags.html', {'bags': bags})


@merchant_required
def create_bag(request):
    if request.method == 'POST':
        form = SurpriseBagForm(request.POST)
        if form.is_valid():
            bag = form.save(commit=False)
            bag.merchant = request.user  # paksa isi pemilik dari session, bukan dari form
            bag.save()
            messages.success(request, f'Surprise Bag "{bag.name}" berhasil dibuat.')
            return redirect('surprise_bag:my_bags')
    else:
        form = SurpriseBagForm()
    return render(request, 'surprise_bag/form.html', {'form': form, 'action': 'Tambah'})


@merchant_required
def edit_bag(request, pk):
    # filter merchant=request.user supaya merchant lain dapat 404
    bag = get_object_or_404(SurpriseBag, pk=pk, merchant=request.user)
    if request.method == 'POST':
        form = SurpriseBagUpdateForm(request.POST, instance=bag)
        if form.is_valid():
            form.save()
            messages.success(request, f'Surprise Bag "{bag.name}" berhasil diperbarui.')
            return redirect('surprise_bag:my_bags')
    else:
        form = SurpriseBagUpdateForm(instance=bag)
    return render(request, 'surprise_bag/form.html', {'form': form, 'action': 'Simpan', 'bag': bag})


@merchant_required
@require_POST
def delete_bag(request, pk):
    bag = get_object_or_404(SurpriseBag, pk=pk, merchant=request.user)
    name = bag.name
    bag.delete()
    messages.success(request, f'Surprise Bag "{name}" berhasil dihapus.')
    return redirect('surprise_bag:my_bags')


# --- AJAX API Views ---

def catalog_api(request):
    """Daftar bag aktif dalam JSON, bisa difilter kategori, harga, stok, dan kata kunci"""
    bags = SurpriseBag.objects.filter(is_active=True).select_related('merchant')

    category = request.GET.get('category')
    if category:
        bags = bags.filter(category=category)

    min_price = _parse_price(request.GET.get('min_price'))
    if min_price is not None:
        bags = bags.filter(discounted_price__gte=min_price)

    max_price = _parse_price(request.GET.get('max_price'))
    if max_price is not None:
        bags = bags.filter(discounted_price__lte=max_price)

    if request.GET.get('available') == '1':
        bags = bags.filter(stock__gt=0)

    q = request.GET.get('q', '').strip()
    if q:
        bags = bags.filter(Q(name__icontains=q) | Q(description__icontains=q))

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        bags = bags.order_by('discounted_price')
    elif sort == 'price_desc':
        bags = bags.order_by('-discounted_price')

    bags = list(bags)
    if sort == 'discount':
        # dihitung di Python karena pembagian Decimal di SQLite kurang akurat
        bags.sort(key=lambda bag: bag.discount_percent, reverse=True)

    return JsonResponse({'bags': [bag.to_dict() for bag in bags], 'count': len(bags)})


def bag_api(request, pk):
    """Data satu bag — dipakai halaman detail untuk refresh stok otomatis"""
    return JsonResponse(_get_visible_bag(request, pk).to_dict())


@merchant_required
@require_POST
def update_stock_api(request, pk):
    """Ubah stok via AJAX. Body: {"delta": 1} atau {"stock": 10}"""
    bag = get_object_or_404(SurpriseBag, pk=pk, merchant=request.user)
    try:
        payload = json.loads(request.body)
        if 'delta' in payload:
            new_stock = bag.stock + int(payload['delta'])
        else:
            new_stock = int(payload['stock'])
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Data stok tidak valid.'}, status=400)

    if new_stock < 0:
        return JsonResponse({'error': 'Stok tidak boleh negatif.'}, status=400)

    bag.stock = new_stock
    bag.save(update_fields=['stock', 'updated_at'])
    return JsonResponse(bag.to_dict())


@merchant_required
@require_POST
def toggle_active_api(request, pk):
    """Aktifkan / nonaktifkan penawaran via AJAX. Body: {"is_active": true}"""
    bag = get_object_or_404(SurpriseBag, pk=pk, merchant=request.user)
    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'error': 'Data tidak valid.'}, status=400)

    bag.is_active = bool(payload.get('is_active', not bag.is_active))
    bag.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse(bag.to_dict())
