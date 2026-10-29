import secrets

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import is_customer, is_merchant
from eco_impact.models import ImpactLog
from surprise_bag.models import SurpriseBag

from .models import Order


@transaction.atomic
def reserve_bag(customer, bag_id, quantity, reservation_key):
    if not is_customer(customer):
        raise PermissionDenied
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 100:
        raise ValidationError('Jumlah paket harus antara 1 dan 100.')
    bag = get_object_or_404(SurpriseBag.objects.select_for_update(), pk=bag_id)
    # Serialisasi reservasi bag ini agar retry tidak mengurangi stok dua kali.
    existing = Order.objects.filter(reservation_key=reservation_key).first()
    if existing:
        if (existing.customer_id != customer.pk or existing.surprise_bag_id != bag.pk
                or existing.quantity != quantity):
            raise ValidationError('Permintaan reservasi tidak cocok. Muat ulang formulir.')
        return existing
    now = timezone.localtime()
    if not bag.is_available or now.time() >= bag.pickup_end:
        raise ValidationError('Paket tidak tersedia atau waktu pickup hari ini sudah berakhir.')
    if bag.merchant_id == customer.pk:
        raise ValidationError('Kamu tidak dapat memesan paket milik sendiri.')
    if not bag.reduce_stock(quantity):
        raise ValidationError('Stok tidak mencukupi. Kurangi jumlah paket atau pilih paket lain.')
    return Order.objects.create(
        customer=customer, surprise_bag=bag, quantity=quantity,
        food_name=bag.name, original_price=bag.original_price,
        discounted_price=bag.discounted_price, pickup_date=now.date(),
        pickup_start=bag.pickup_start, pickup_end=bag.pickup_end, reservation_key=reservation_key,
    )


@transaction.atomic
def transition_order(actor, order_id, action, pickup_code=''):
    orders = Order.objects.select_for_update()
    if action == 'cancel':
        if not is_customer(actor):
            raise PermissionDenied
        orders = orders.filter(customer=actor)
        expected, target = Order.Status.PENDING, Order.Status.CANCELLED
    else:
        if not is_merchant(actor):
            raise PermissionDenied
        orders = orders.filter(surprise_bag__merchant=actor)
        if action == 'ready':
            expected, target = Order.Status.PENDING, Order.Status.READY_TO_PICKUP
        elif action == 'complete':
            expected, target = Order.Status.READY_TO_PICKUP, Order.Status.COMPLETED
        else:
            raise ValidationError('Aksi tidak valid.')
    order = get_object_or_404(orders, pk=order_id)
    if order.status != expected:
        raise ValidationError('Status pesanan sudah berubah. Perbarui daftar pesanan.')
    if action == 'complete' and not secrets.compare_digest(order.pickup_code, pickup_code.upper()):
        raise ValidationError('Kode pickup tidak cocok. Periksa kode dari customer.')
    now = timezone.now()
    completed_at = now if target == Order.Status.COMPLETED else None
    if not Order.objects.filter(pk=order.pk, status=expected).update(
            status=target, updated_at=now, completed_at=completed_at):
        raise ValidationError('Status pesanan sudah berubah. Perbarui daftar pesanan.')
    if action == 'cancel':
        SurpriseBag.objects.filter(pk=order.surprise_bag_id).update(stock=F('stock') + order.quantity)
    elif action == 'complete':
        ImpactLog.objects.get_or_create(
            source='order', order_id=order.pk,
            defaults={'user': order.customer, 'food_name': order.food_name,
                      'quantity': order.quantity, 'original_price': order.original_price,
                      'discounted_price': order.discounted_price},
        )
    order.refresh_from_db()
    return order
