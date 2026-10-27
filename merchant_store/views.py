import math

from django.contrib import messages
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.permissions import is_customer

from .decorators import customer_required, customer_required_api, merchant_required
from .forms import MerchantStoreForm
from .models import MerchantStore, StoreWishlist
from .ratings import get_rating, get_rating_map
from .services import GeocodingError, bounding_box, geocode_address, haversine_km

# Titik awal peta: kampus UI Depok
DEFAULT_CENTER = {'lat': -6.3628, 'lng': 106.8272}
RADIUS_CHOICES = [1, 3, 5]
MAX_RADIUS_KM = 50
MAX_RESULTS = 100
GEOCODE_LIMIT_PER_MINUTE = 20


# Helper
def _own_store(user):
    return MerchantStore.objects.filter(owner=user).first()


def _geocode_into(request, store):
    """Isi latitude/longitude toko dari alamatnya. Gagal tidak membatalkan penyimpanan."""
    try:
        result = geocode_address(store.address)
    except GeocodingError:
        store.latitude = store.longitude = None
        messages.warning(
            request,
            'Toko tersimpan, tetapi layanan peta (OpenStreetMap) sedang tidak dapat dihubungi. '
            'Buka "Edit Toko" lalu simpan ulang beberapa saat lagi untuk memuat lokasi peta.',
        )
        return
    if result is None:
        store.latitude = store.longitude = None
        messages.warning(
            request,
            'Toko tersimpan, tetapi alamat belum ditemukan di peta. '
            'Coba perbarui alamat dengan nama jalan, kelurahan, dan kota yang lebih jelas.',
        )
        return
    store.latitude, store.longitude = result['lat'], result['lng']


def _parse_float(raw, low, high):
    """None jika kosong; ValueError jika bukan angka valid / di luar rentang."""
    if raw is None or str(raw).strip() == '':
        return None
    value = float(raw)
    if not math.isfinite(value) or not (low <= value <= high):
        raise ValueError
    return value


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _is_throttled(request):
    key = f'geocode-throttle:{_client_ip(request)}'
    cache.add(key, 0, 60)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, 60)
        count = 1
    return count > GEOCODE_LIMIT_PER_MINUTE


def _wishlisted_ids(user):
    if user.is_authenticated and is_customer(user):
        return set(StoreWishlist.objects.filter(customer=user).values_list('store_id', flat=True))
    return set()


def _serialize_store(store, distance_km, rating_map, wishlisted_ids, can_wishlist):
    average, count = rating_map.get(store.id, (None, 0))
    data = {
        'id': store.id,
        'name': store.name,
        'address': store.address,
        'phone': store.phone,
        'hours': store.hours_display,
        'is_open': store.is_open_now(),
        'latitude': store.latitude,
        'longitude': store.longitude,
        'distance_km': None if distance_km is None else round(distance_km, 2),
        'rating': average,
        'rating_count': count,
        'bag_count': getattr(store, 'bag_count', 0),
        'detail_url': reverse('merchant_store:detail', args=[store.id]),
    }
    if can_wishlist:
        data['wishlisted'] = store.id in wishlisted_ids
        data['wishlist_url'] = reverse('merchant_store:wishlist_toggle', args=[store.id])
    return data


# READ (publik: Guest, Customer, Merchant)
@require_GET
def store_list(request):
    """Halaman direktori + peta. Datanya dimuat asinkron lewat store_search_api."""
    return render(request, 'merchant_store/list.html', {
        'default_center': DEFAULT_CENTER,
        'radius_choices': RADIUS_CHOICES,
        'can_wishlist': is_customer(request.user),
    })


@require_GET
def store_search_api(request):
    """GET ?q=&lat=&lng=&radius=  ->  JSON daftar toko aktif (terdekat lebih dulu)."""
    try:
        lat = _parse_float(request.GET.get('lat'), -90, 90)
        lng = _parse_float(request.GET.get('lng'), -180, 180)
        radius = _parse_float(request.GET.get('radius'), 0.1, MAX_RADIUS_KM)
    except ValueError:
        return JsonResponse({'error': 'Parameter lat, lng, atau radius tidak valid.'}, status=400)

    if (lat is None) != (lng is None):
        return JsonResponse({'error': 'lat dan lng harus dikirim bersamaan.'}, status=400)
    if radius is not None and lat is None:
        return JsonResponse({'error': 'Tentukan lokasi Anda terlebih dahulu untuk memakai filter radius.'}, status=400)

    stores = MerchantStore.objects.filter(is_active=True).annotate(
        bag_count = Count(
            'owner__surprise_bags',
            filter=Q(owner__surprise_bags__is_active=True, owner__surprise_bags__stock__gt=0),
        ),
    )

    query = request.GET.get('q', '').strip()
    if query:
        stores = stores.filter(
            Q(name__icontains=query) | Q(address__icontains=query) | Q(description__icontains=query)
        )

    if radius is not None:
        min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius)
        stores = stores.filter(
            latitude__range=(min_lat, max_lat), longitude__range=(min_lng, max_lng),
        )

    rows = []
    for store in stores:
        distance = None
        if lat is not None and store.has_coordinates:
            distance = haversine_km(lat, lng, store.latitude, store.longitude)
        if radius is not None and (distance is None or distance > radius):
            continue
        rows.append((store, distance))

    if lat is not None:
        # toko tanpa koordinat ditaruh paling belakang
        rows.sort(key=lambda row: (row[1] is None, row[1] or 0, row[0].name.lower()))
    rows = rows[:MAX_RESULTS]

    rating_map = get_rating_map([store.id for store, _ in rows])
    wishlisted = _wishlisted_ids(request.user)
    can_wishlist = is_customer(request.user)
    return JsonResponse({
        'count': len(rows),
        'can_wishlist': can_wishlist,
        'stores': [
            _serialize_store(store, distance, rating_map, wishlisted, can_wishlist)
            for store, distance in rows
        ],
    })


@require_GET
def geocode_api(request):
    """GET ?q=alamat -> koordinat dari OpenStreetMap Nominatim (dipakai peta & form toko)."""
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return JsonResponse({'error': 'Masukkan minimal 3 karakter.'}, status=400)
    if len(query) > 255:
        return JsonResponse({'error': 'Teks pencarian terlalu panjang.'}, status=400)
    if _is_throttled(request):
        return JsonResponse({'error': 'Terlalu banyak permintaan. Coba lagi sebentar lagi.'}, status=429)
    try:
        result = geocode_address(query)
    except GeocodingError:
        return JsonResponse({'error': 'Layanan peta sedang tidak dapat dihubungi. Coba lagi nanti.'}, status=502)
    if result is None:
        return JsonResponse({'error': 'Lokasi tidak ditemukan. Coba kata kunci yang lebih spesifik.'}, status=404)
    return JsonResponse(result)


@require_GET
def store_detail(request, pk):
    store = get_object_or_404(MerchantStore, pk=pk)
    is_owner = request.user.is_authenticated and store.owner_id == request.user.id
    if not store.is_active and not is_owner:
        raise Http404
    average, count = get_rating(store.id)
    can_wishlist = is_customer(request.user)
    return render(request, 'merchant_store/detail.html', {
        'store': store,
        'is_owner': is_owner,
        'rating_average': average,
        'rating_count': count,
        'can_wishlist': can_wishlist,
        'is_wishlisted': store.id in _wishlisted_ids(request.user),
    })


# CREATE / UPDATE / DELETE (khusus Merchant pemilik toko)
# Tidak ada ID toko di URL "my/..." sehingga merchant hanya bisa menyentuh tokonya sendiri.
@merchant_required
@require_GET
def my_store(request):
    store = _own_store(request.user)
    average, count = get_rating(store.id) if store else (None, 0)
    return render(request, 'merchant_store/my_store.html', {
        'store': store,
        'rating_average': average,
        'rating_count': count,
    })


@merchant_required
@require_http_methods(['GET', 'POST'])
def store_create(request):
    if _own_store(request.user):
        messages.info(request, 'Kamu sudah memiliki profil toko. Silakan edit dari halaman Toko Saya.')
        return redirect('merchant_store:my_store')

    form = MerchantStoreForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        store = form.save(commit=False)
        store.owner = request.user
        _geocode_into(request, store)
        try:
            with transaction.atomic():
                store.save()
        except IntegrityError:
            messages.info(request, 'Profil toko sudah ada.')
            return redirect('merchant_store:my_store')
        messages.success(request, 'Profil toko berhasil dibuat.')
        return redirect('merchant_store:my_store')
    return render(request, 'merchant_store/form.html', {'form': form, 'is_edit': False})


@merchant_required
@require_http_methods(['GET', 'POST'])
def store_edit(request):
    store = _own_store(request.user)
    if store is None:
        messages.info(request, 'Kamu belum memiliki profil toko. Buat dulu di sini.')
        return redirect('merchant_store:create')

    form = MerchantStoreForm(request.POST or None, instance=store)
    if request.method == 'POST' and form.is_valid():
        address_changed = 'address' in form.changed_data
        store = form.save(commit=False)
        if address_changed or not store.has_coordinates:
            _geocode_into(request, store)
        store.save()
        messages.success(request, 'Profil toko berhasil diperbarui.')
        return redirect('merchant_store:my_store')
    return render(request, 'merchant_store/form.html', {'form': form, 'is_edit': True, 'store': store})


@merchant_required
@require_POST
def store_toggle_active(request):
    store = get_object_or_404(MerchantStore, owner=request.user)
    store.is_active = not store.is_active
    store.save(update_fields=['is_active', 'updated_at'])
    if store.is_active:
        messages.success(request, 'Toko diaktifkan kembali dan tampil di direktori.')
    else:
        messages.success(request, 'Toko dinonaktifkan dan disembunyikan dari direktori.')
    return redirect('merchant_store:my_store')


@merchant_required
@require_POST
def store_delete(request):
    store = get_object_or_404(MerchantStore, owner=request.user)
    store.delete()
    messages.success(request, 'Profil toko berhasil dihapus.')
    return redirect('merchant_store:my_store')


# WISHLIST (khusus Customer)
@customer_required
@require_GET
def wishlist_list(request):
    items = (
        StoreWishlist.objects.filter(customer=request.user)
        .select_related('store')
    )
    rating_map = get_rating_map([item.store_id for item in items])
    stores = []
    for item in items:
        average, count = rating_map.get(item.store_id, (None, 0))
        stores.append({'store': item.store, 'rating_average': average, 'rating_count': count})
    return render(request, 'merchant_store/wishlist.html', {'entries': stores})


@customer_required_api
@require_POST
def wishlist_toggle(request, pk):
    store = get_object_or_404(MerchantStore, pk=pk)
    existing = StoreWishlist.objects.filter(customer=request.user, store=store)
    if existing.exists():
        existing.delete()
        return JsonResponse({'wishlisted': False})
    if not store.is_active:
        return JsonResponse({'error': 'Toko ini sedang tidak aktif.'}, status=404)
    StoreWishlist.objects.get_or_create(customer=request.user, store=store)
    return JsonResponse({'wishlisted': True})
