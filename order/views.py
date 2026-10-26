from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.cache import never_cache

from accounts.permissions import is_customer, is_merchant
from surprise_bag.models import SurpriseBag

from .forms import OrderForm, PickupVerificationForm
from .models import Order
from .services import reserve_bag, transition_order


def _visible_orders(user):
    orders = Order.objects.select_related('customer', 'surprise_bag__merchant')
    if is_customer(user):
        return orders.filter(customer=user)
    if is_merchant(user):
        return orders.filter(surprise_bag__merchant=user)
    raise PermissionDenied


def _order_context(request):
    orders = _visible_orders(request.user)
    status = request.GET.get('status', '')
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    return {'orders': orders, 'is_customer': is_customer(request.user),
            'is_merchant': is_merchant(request.user), 'statuses': Order.Status.choices,
            'selected_status': status}


@login_required
@never_cache
@require_GET
def order_list(request):
    return render(request, 'order/list.html', _order_context(request))


@login_required
@never_cache
@require_GET
def orders_api(request):
    html = render_to_string('order/components/order_cards.html', _order_context(request), request=request)
    return JsonResponse({'html': html})


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def create_order(request, bag_id):
    if not is_customer(request.user):
        raise PermissionDenied
    bag = get_object_or_404(SurpriseBag, pk=bag_id, is_active=True)
    form = OrderForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            reserve_bag(request.user, bag.pk, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
            bag.refresh_from_db()
        except IntegrityError:
            form.add_error(None, 'Permintaan reservasi sudah dipakai. Muat ulang formulir lalu coba kembali.')
        else:
            messages.success(request, 'Reservasi berhasil dibuat. Pantau status pickup di pesananmu.')
            return redirect('order:list')
    return render(request, 'order/form.html', {'form': form, 'bag': bag})


@login_required
@never_cache
@require_POST
def update_order_api(request, pk, action):
    get_object_or_404(_visible_orders(request.user), pk=pk)
    pickup_code = ''
    if action == 'complete':
        form = PickupVerificationForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'error': 'Masukkan kode pickup 8 karakter dari customer.'}, status=400)
        pickup_code = form.cleaned_data['pickup_code']
    try:
        order = transition_order(request.user, pk, action, pickup_code)
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=409)
    return JsonResponse({'id': str(order.pk), 'status': order.status,
                         'message': f'Status pesanan diperbarui: {order.get_status_display()}.'})
