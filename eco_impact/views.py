from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import ImpactLog
from .forms import ImpactLogForm


@login_required
def dashboard(request):
    # halaman utama — data diisi via AJAX, jadi view ini cukup render template kosong
    return render(request, 'eco_impact/dashboard.html')


@login_required
def log_list(request):
    # ambil semua log milik user yang sedang login saja
    logs = ImpactLog.objects.filter(user=request.user)
    return render(request, 'eco_impact/log_list.html', {'logs': logs})


@login_required
def create_log(request):
    if request.method == 'POST':
        form = ImpactLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)  # belum disimpan dulu
            log.user = request.user        # paksa isi user dari session, bukan dari form
            log.source = 'manual'          # log buatan sendiri = manual
            log.save()
            return redirect('eco_impact:dashboard')
    else:
        form = ImpactLogForm()
    return render(request, 'eco_impact/form.html', {'form': form, 'action': 'Tambah'})


@login_required
def edit_log(request, pk):
    # pastikan log ini punya user yang login, bukan punya orang lain
    log = get_object_or_404(ImpactLog, pk=pk, user=request.user)

    # log otomatis dari order tidak boleh diedit
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
    log = get_object_or_404(ImpactLog, pk=pk, user=request.user)
    # hanya log manual yang boleh dihapus user
    if log.source == 'manual':
        log.delete()
    return redirect('eco_impact:dashboard')


# --- AJAX API Views ---
# dua view ini dipanggil dari JavaScript, bukan dari halaman biasa

@login_required
def summary_api(request):
    """Ringkasan metrik (total hemat, total karbon, jumlah log) dalam JSON"""
    period = request.GET.get('period', 'all')  # bisa: weekly, monthly, all
    logs = ImpactLog.objects.filter(user=request.user)

    # filter berdasarkan periode yang dipilih
    if period == 'weekly':
        logs = logs.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif period == 'monthly':
        logs = logs.filter(created_at__gte=timezone.now() - timedelta(days=30))

    # kalkulasi pakai property dari model
    total_saved = sum(log.money_saved for log in logs)
    total_carbon = sum(log.carbon_prevented_kg for log in logs)

    return JsonResponse({
        'total_money_saved': float(total_saved),
        'total_carbon_kg': total_carbon,
        'total_logs': logs.count(),
        'period': period,
    })


@login_required
def logs_api(request):
    """Daftar log dalam JSON, bisa difilter per periode"""
    period = request.GET.get('period', 'all')
    logs = ImpactLog.objects.filter(user=request.user)

    if period == 'weekly':
        logs = logs.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif period == 'monthly':
        logs = logs.filter(created_at__gte=timezone.now() - timedelta(days=30))

    data = [{
        'id': str(log.id),
        'food_name': log.food_name,
        'quantity': log.quantity,
        'money_saved': float(log.money_saved),
        'carbon_kg': log.carbon_prevented_kg,
        'source': log.get_source_display(),  # tampil label yang readable, bukan kode
        'notes': log.notes,
        'date': log.created_at.strftime('%d %b %Y'),
    } for log in logs]

    return JsonResponse({'logs': data})