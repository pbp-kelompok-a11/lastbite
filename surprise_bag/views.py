import json
import math
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.views.decorators.http import require_POST
from accounts.permissions import is_customer, is_merchant

from .forms import SurpriseBagForm, SurpriseBagUpdateForm
from .models import SurpriseBag

CATALOG_PAGE_SIZE = 12  # 12 pas untuk grid 3 atau 4 kolom
CATALOG_SORT_CHOICES = [
    ('nearest', 'Terdekat'),
    ('newest', 'Terbaru'),
    ('price_asc', 'Harga termurah'),
    ('price_desc', 'Harga termahal'),
    ('discount', 'Diskon terbesar'),
]

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

def _parse_coordinate(value, limit):
    # lat/lng dari browser, dibatasi ke rentang yang valid (lat ±90, lng ±180)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and -limit <= number <= limit else None

def _distance_km(lat1, lng1, lat2, lng2):
    """Jarak garis lurus dua titik di bumi (rumus haversine)."""
    lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))

def _attach_distances(bags, lat, lng):
    """Isi bag.distance_km dari koordinat toko (Modul Merchant Store) ke lokasi pengguna."""
    for bag in bags:
        store = getattr(bag.merchant, 'merchant_store', None)
        if store is not None and store.has_coordinates:
            bag.distance_km = _distance_km(lat, lng, store.latitude, store.longitude)

def _get_visible_bag(request, pk):
    # bag nonaktif hanya boleh dilihat pemiliknya
    bag = get_object_or_404(SurpriseBag.objects.select_related('merchant', 'merchant__merchant_store'), pk=pk)
    if not bag.is_active and bag.merchant != request.user:
        raise Http404
    return bag

def _catalog_filters(params):
    """Bersihkan filter katalog dari query string; nilai yang tidak dikenal kembali ke default."""
    category = params.get('category', '')
    sort = params.get('sort', 'newest')
    min_price = _parse_price(params.get('min_price'))
    max_price = _parse_price(params.get('max_price'))
    lat = _parse_coordinate(params.get('lat'), 90)
    lng = _parse_coordinate(params.get('lng'), 180)
    has_location = lat is not None and lng is not None
    return {
        'q': params.get('q', '').strip(),
        'category': category if category in dict(SurpriseBag.CATEGORY_CHOICES) else '',
        'min_price': '' if min_price is None else str(min_price),
        'max_price': '' if max_price is None else str(max_price),
        'sort': sort if sort in dict(CATALOG_SORT_CHOICES) else 'newest',
        'stock': 'all' if params.get('stock') == 'all' else 'available',
        'lat': f'{lat:.5f}' if has_location else '',
        'lng': f'{lng:.5f}' if has_location else '',
    }


def _filter_bags(filters):
    """Terapkan filter katalog dan kembalikan list bag aktif yang sudah diurutkan."""
    bags = SurpriseBag.objects.filter(is_active=True).select_related('merchant', 'merchant__merchant_store')
    if filters['category']:
        bags = bags.filter(category=filters['category'])
    if filters['min_price']:
        bags = bags.filter(discounted_price__gte=Decimal(filters['min_price']))
    if filters['max_price']:
        bags = bags.filter(discounted_price__lte=Decimal(filters['max_price']))
    if filters['stock'] == 'available':
        bags = bags.filter(stock__gt=0)
    if filters['q']:
        bags = bags.filter(Q(name__icontains=filters['q']) | Q(description__icontains=filters['q']))

    # urutan selalu diberi pembanding cadangan supaya isi tiap halaman stabil
    ordering = {
        'newest': ('-created_at', 'pk'),
        'nearest': ('-created_at', 'pk'),  # cadangan kalau lokasi pengguna tidak ada
        'price_asc': ('discounted_price', '-created_at', 'pk'),
        'price_desc': ('-discounted_price', '-created_at', 'pk'),
        'discount': ('-created_at', 'pk'),
    }
    bags = list(bags.order_by(*ordering[filters['sort']]))
    if filters['sort'] == 'discount':
        # dihitung di Python karena pembagian Decimal di SQLite kurang akurat
        bags.sort(key=lambda bag: bag.discount_percent, reverse=True)

    if filters['lat']:
        _attach_distances(bags, float(filters['lat']), float(filters['lng']))
        if filters['sort'] == 'nearest':
            # toko yang belum punya koordinat ditaruh paling belakang
            bags.sort(key=lambda bag: (bag.distance_km is None, bag.distance_km or 0))
    return bags


def _page_numbers(paginator, page_obj):
    """Nomor halaman dengan elipsis, sama seperti pagination di modul Community."""
    if paginator.num_pages <= 7:
        return list(paginator.page_range)
    visible_pages = {1, paginator.num_pages}
    visible_pages.update(range(max(1, page_obj.number - 2), min(paginator.num_pages, page_obj.number + 2) + 1))
    page_numbers = []
    previous = 0
    for number in sorted(visible_pages):
        if number - previous > 1:
            page_numbers.append(paginator.ELLIPSIS)
        page_numbers.append(number)
        previous = number
    return page_numbers


# --- Halaman publik (Guest & Customer) ---

def catalog(request):
    filters = _catalog_filters(request.GET)
    paginator = Paginator(_filter_bags(filters), CATALOG_PAGE_SIZE)
    # get_page aman untuk nomor halaman ngawur / kelewatan (otomatis ke halaman terdekat)
    page_obj = paginator.get_page(request.GET.get('page'))

    # hanya filter yang bukan default yang ikut ke URL, biar link halaman tetap ringkas
    defaults = _catalog_filters({})
    filter_params = {key: value for key, value in filters.items() if value != defaults[key]}

    # request AJAX cukup dikirimi potongan hasilnya saja (pola yang sama dengan modul Community)
    template = 'surprise_bag/catalog.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'surprise_bag/components/catalog_results.html'
    return render(request, template, {
        'bags': page_obj.object_list,
        'page_obj': page_obj,
        'page_numbers': _page_numbers(paginator, page_obj),
        'page_query_prefix': f'{urlencode(filter_params)}&' if filter_params else '',
        'filters': filters,
        'categories': SurpriseBag.CATEGORY_CHOICES,
        'sort_options': CATALOG_SORT_CHOICES,
        'is_merchant': is_merchant(request.user),
    })


def bag_detail(request, pk):
    bag = _get_visible_bag(request, pk)
    return render(request, 'surprise_bag/detail.html', {
        'bag': bag,
        'is_owner': bag.merchant == request.user,
        'is_customer': is_customer(request.user),
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
    try:
        bag.delete()
    except ProtectedError:
        bag.is_active = False
        bag.save(update_fields=['is_active', 'updated_at'])
        messages.success(request, f'Paket "{name}" dinonaktifkan karena memiliki riwayat pesanan.')
        return redirect('surprise_bag:my_bags')
    messages.success(request, f'Surprise Bag "{name}" berhasil dihapus.')
    return redirect('surprise_bag:my_bags')


# --- AJAX API Views ---

def catalog_api(request):
    """Daftar bag aktif dalam JSON (tanpa pagination) — filternya sama dengan halaman katalog"""
    filters = _catalog_filters(request.GET)
    # API ini sejak awal memakai ?available=1 untuk filter stok, jadi tetap didukung
    filters['stock'] = 'available' if request.GET.get('available') == '1' else 'all'
    bags = _filter_bags(filters)
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
