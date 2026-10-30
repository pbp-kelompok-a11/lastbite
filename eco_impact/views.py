from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from accounts.permissions import is_customer
from .models import ImpactLog
from .forms import ImpactLogForm


@login_required
def dashboard(request):
    """Halaman visual dashboard Eco Impact (hanya untuk Customer)."""
    if not is_customer(request.user):
        raise PermissionDenied
    return render(request, 'eco_impact/dashboard.html')


@login_required
def log_list(request):
    """Daftar log milik pengguna yang sedang login."""
    if not is_customer(request.user):
        raise PermissionDenied
    logs = ImpactLog.objects.filter(user=request.user)
    return render(request, 'eco_impact/log_list.html', {'logs': logs})


@login_required
def create_log(request):
    """Pencatatan manual penyelamatan makanan oleh customer."""
    if not is_customer(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = ImpactLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.source = 'manual'
            log.save()
            return redirect('eco_impact:dashboard')
    else:
        form = ImpactLogForm()
    return render(request, 'eco_impact/form.html', {'form': form, 'action': 'Tambah'})


@login_required
def edit_log(request, pk):
    """Edit data log manual milik customer sendiri."""
    if not is_customer(request.user):
        raise PermissionDenied

    log = get_object_or_404(ImpactLog, pk=pk, user=request.user)
    # Log otomatis dari pesanan (order) tidak boleh diedit manual
    if log.source == 'order':
        return redirect('eco_impact:dashboard')

    if request.method == 'POST':
        form = ImpactLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('eco_impact:dashboard')
    else:
        form = ImpactLogForm(instance=log)
    return render(request, 'eco_impact/form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_log(request, pk):
    """Hapus log manual milik customer sendiri."""
    if not is_customer(request.user):
        raise PermissionDenied
    log = get_object_or_404(ImpactLog, pk=pk, user=request.user)
    if log.source == 'manual':
        log.delete()
    return redirect('eco_impact:dashboard')


# --- AJAX API Views ---

@login_required
def summary_api(request):
    """
    Mengembalikan data agregasi metrik, tren bulanan, dan status level
    berdasarkan data riil database pengguna yang login.
    """
    if not is_customer(request.user):
        raise PermissionDenied

    period = request.GET.get('period', 'monthly')  # monthly atau weekly
    all_user_logs = ImpactLog.objects.filter(user=request.user)

    now = timezone.now()
    if period == 'weekly':
        filtered_logs = all_user_logs.filter(created_at__gte=now - timedelta(days=7))
    elif period == 'monthly':
        filtered_logs = all_user_logs.filter(created_at__gte=now - timedelta(days=30))
    else:
        filtered_logs = all_user_logs

    # Metrik kartu periode
    total_bags = sum(l.quantity for l in filtered_logs)
    total_food_kg = round(total_bags * 0.3, 1)
    total_carbon_kg = round(sum(l.carbon_prevented_kg for l in filtered_logs), 1)
    total_saved = sum(l.money_saved for l in filtered_logs)
    
    # 1 kg CO2 setara dengan ~4 km perjalanan mobil penumpang (faktor standar IPCC/EPA)
    equivalent_km = int(round(total_carbon_kg * 4.0))

    # Format penghematan rupiah (misal: 426rb atau Rp 426.000)
    saved_int = int(total_saved)
    if saved_int >= 1000000:
        money_display = f"{round(saved_int / 1000000, 1)} jt"
    elif saved_int >= 1000:
        money_display = f"{saved_int // 1000} rb"
    else:
        money_display = f"{saved_int}"

    # Tren 6 bulan terakhir dari log nyata pengguna
    months_data = []
    month_names_id = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    
    for i in range(5, -1, -1):
        local_now = timezone.localtime(now)
        year, month_index = divmod(local_now.year * 12 + local_now.month - 1 - i, 12)
        m_start = local_now.replace(year=year, month=month_index + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        m_next = (m_start + timedelta(days=32)).replace(day=1)
        
        m_logs = all_user_logs.filter(created_at__gte=m_start, created_at__lt=m_next)
        m_carbon = round(sum(l.carbon_prevented_kg for l in m_logs), 1)
        months_data.append({
            'label': month_names_id[m_start.month - 1],
            'carbon_kg': m_carbon,
        })

    max_carbon = max([m['carbon_kg'] for m in months_data] + [1.0])
    for m in months_data:
        m['percent'] = int(round((m['carbon_kg'] / max_carbon) * 100)) if m['carbon_kg'] > 0 else 0

    # Metrik Level & Gamifikasi All-Time
    all_time_bags = sum(l.quantity for l in all_user_logs)
    
    if all_time_bags < 5:
        level_num = 1
        level_name = "Seedling Saver"
        target_bags = 5
        next_name = "Food Rescuer"
        progress_pct = int(round((all_time_bags / 5) * 100))
    elif all_time_bags < 12:
        level_num = 2
        level_name = "Food Rescuer"
        target_bags = 12
        next_name = "Waste Warrior"
        progress_pct = int(round((all_time_bags / 12) * 100))
    elif all_time_bags < 20:
        level_num = 3
        level_name = "Waste Warrior"
        target_bags = 20
        next_name = "Planet Protector"
        progress_pct = int(round((all_time_bags / 20) * 100))
    else:
        level_num = 4
        level_name = "Planet Protector"
        target_bags = all_time_bags
        next_name = "Earth Guardian"
        progress_pct = 100

    rem_bags = max(0, target_bags - all_time_bags)
    if rem_bags > 0:
        level_desc = f"Kamu sudah menyelamatkan {all_time_bags} bag. Sedikit lagi menuju {next_name}!"
    else:
        level_desc = f"Luar biasa! Kamu sudah menyelamatkan {all_time_bags} bag dan mencapai level tertinggi!"

    return JsonResponse({
        'total_food_kg': total_food_kg,
        'total_carbon_kg': total_carbon_kg,
        'total_money_saved': float(total_saved),
        'money_saved_display': money_display,
        'total_bags_count': total_bags,
        'equivalent_km': equivalent_km,
        'period': period,
        'monthly_trend': months_data,
        'level': {
            'number': level_num,
            'name': level_name,
            'description': level_desc,
            'current_bags': all_time_bags,
            'target_bags': target_bags,
            'progress_pct': min(100, max(0, progress_pct)),
        },
    })


@login_required
def logs_api(request):
    """
    Mengembalikan daftar log pengguna yang difilter per periode dalam JSON.
    Mengambil nama toko dari relasi Order jika bersumber dari pesanan,
    atau menggunakan catatan bila manual.
    """
    if not is_customer(request.user):
        raise PermissionDenied

    period = request.GET.get('period', 'monthly')
    logs = ImpactLog.objects.filter(user=request.user)
    now = timezone.now()

    if period == 'weekly':
        logs = logs.filter(created_at__gte=now - timedelta(days=7))
    elif period == 'monthly':
        logs = logs.filter(created_at__gte=now - timedelta(days=30))

    order_ids = [l.order_id for l in logs if l.source == 'order' and l.order_id]
    orders_map = {}
    if order_ids:
        from order.models import Order
        orders = Order.objects.filter(pk__in=order_ids).select_related('surprise_bag__merchant__merchant_store')
        for ord_obj in orders:
            store = getattr(ord_obj.surprise_bag.merchant, 'merchant_store', None)
            orders_map[ord_obj.pk] = store.name if store else '[Nama Toko]'

    month_names_id = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    data = []
    for log in logs:
        if log.source == 'order':
            store_name = orders_map.get(log.order_id, '[Nama Toko]')
        else:
            store_name = log.notes.strip() if log.notes.strip() else '[Nama Toko]'

        # Format tanggal rapi: "12 Oktober 2026"
        dt = timezone.localtime(log.created_at)
        formatted_date = f"{dt.day} {month_names_id[dt.month - 1]} {dt.year}"

        data.append({
            'id': str(log.id),
            'store_name': store_name,
            'food_name': log.food_name,
            'quantity': log.quantity,
            'food_weight_kg': round(log.quantity * 0.3, 1),
            'money_saved': float(log.money_saved),
            'carbon_prevented_kg': round(log.carbon_prevented_kg, 1),
            'source': log.source,
            'source_display': log.get_source_display(),
            'notes': log.notes,
            'formatted_date': formatted_date,
        })

    return JsonResponse({'logs': data})
