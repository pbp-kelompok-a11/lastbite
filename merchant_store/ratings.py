
"""Menghitung rating toko dari rating customer dan review terverifikasi."""

from collections import defaultdict

from django.db.models import F

from community.models import CommunityPost

from .models import MerchantStore, StoreRating


def get_rating_map(store_ids):
    """
    Menghasilkan:
        {store_id: (rata_rata, jumlah_rating)}

    Rating langsung customer dan review pesanan selesai digabung.
    Jika customer sudah memberi rating langsung, review miliknya
    untuk toko yang sama tidak dihitung dua kali.
    """

    store_ids = list(set(store_ids))

    if not store_ids:
        return {}

    # Mapping ID pemilik merchant ke ID toko.
    owner_to_store = dict(
        MerchantStore.objects
        .filter(pk__in=store_ids)
        .values_list('owner_id', 'pk')
    )

    if not owner_to_store:
        return {}

    totals = defaultdict(float)
    counts = defaultdict(int)
    direct_pairs = set()

    # Rating langsung yang diberikan customer.
    direct_rows = StoreRating.objects.filter(
        store_id__in=store_ids
    ).values(
        'store_id',
        'customer_id',
        'rating',
    )

    for row in direct_rows:
        store_id = row['store_id']

        totals[store_id] += row['rating']
        counts[store_id] += 1

        direct_pairs.add(
            (store_id, row['customer_id'])
        )

    # Review lama dari Community untuk pesanan yang selesai.
    review_rows = CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.REVIEW,
        related_order__status='completed',
        related_order__customer_id=F('author_id'),
        related_order__surprise_bag__merchant_id__in=list(
            owner_to_store.keys()
        ),
        rating__isnull=False,
    ).values(
        'author_id',
        'rating',
        'related_order__surprise_bag__merchant_id',
    )

    for row in review_rows:
        store_id = owner_to_store.get(
            row['related_order__surprise_bag__merchant_id']
        )

        if store_id is None:
            continue

        # Hindari menghitung dua kali customer yang sudah
        # memberikan rating langsung untuk toko ini.
        if (store_id, row['author_id']) in direct_pairs:
            continue

        totals[store_id] += row['rating']
        counts[store_id] += 1

    return {
        store_id: (
            round(totals[store_id] / counts[store_id], 1),
            counts[store_id],
        )
        for store_id in counts
        if counts[store_id] > 0
    }


def get_rating(store_id):
    """Mengembalikan (rata-rata, jumlah); None dan 0 jika belum ada."""
    return get_rating_map([store_id]).get(store_id, (None, 0))
