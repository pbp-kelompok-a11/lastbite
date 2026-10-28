from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models import Case, Count, IntegerField, OuterRef, Q, Subquery, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.cache import never_cache

from accounts.permissions import is_customer, is_merchant
from surprise_bag.models import SurpriseBag
from community.models import CommunityPost

from .forms import OrderForm, PickupVerificationForm
from .models import Order
from .services import reserve_bag, transition_order


def _visible_orders(user):
    reviews = CommunityPost.objects.filter(related_order=OuterRef('pk'), post_type='review')
    orders = Order.objects.select_related('customer', 'surprise_bag__merchant__merchant_store').annotate(
        review_id=Subquery(reviews.values('pk')[:1]),
    )
    if is_customer(user):
        return orders.filter(customer=user)
    if is_merchant(user):
        return orders.filter(surprise_bag__merchant=user)
    raise PermissionDenied


def _order_context(request):
    orders = _visible_orders(request.user)
    status = request.GET.get('status', '')
    if status not in Order.Status.values:
        status = ''
    active_statuses = [Order.Status.PENDING, Order.Status.READY_TO_PICKUP]
    history_statuses = [Order.Status.COMPLETED, Order.Status.CANCELLED]
    default_tab = 'history' if status in history_statuses else 'active'
    tab = request.GET.get('tab', default_tab)
    if tab not in ('active', 'history'):
        tab = default_tab
    counts = orders.aggregate(
        active_count=Count('pk', filter=Q(status__in=active_statuses)),
        history_count=Count('pk', filter=Q(status__in=history_statuses)),
    )
    tab_statuses = active_statuses if tab == 'active' else history_statuses
    orders = orders.filter(status__in=tab_statuses)
    if status in tab_statuses:
        orders = orders.filter(status=status)
    else:
        status = ''
    orders = orders.annotate(
        pickup_priority=Case(When(status=Order.Status.READY_TO_PICKUP, then=0),
                             default=1, output_field=IntegerField()),
    ).order_by('pickup_priority', '-created_at', '-pk')
    return {'orders': orders, 'is_customer': is_customer(request.user),
            'is_merchant': is_merchant(request.user),
            'statuses': [(value, label) for value, label in Order.Status.choices if value in tab_statuses],
            'selected_status': status, 'selected_tab': tab, 'today': timezone.localdate(), **counts}


@login_required
@never_cache
@require_GET
def order_list(request):
    return render(request, 'order/list.html', _order_context(request))


@login_required
@never_cache
@require_GET
def orders_api(request):
    context = _order_context(request)
    html = render_to_string('order/components/order_cards.html', context, request=request)
    return JsonResponse({'html': html, 'active_count': context['active_count'],
                         'history_count': context['history_count'], 'tab': context['selected_tab'],
                         'statuses': context['statuses'], 'selected_status': context['selected_status']})


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
