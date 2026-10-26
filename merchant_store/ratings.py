"""Rating toko dari review pesanan selesai, menggunakan owner SurpriseBag asli."""
from django.db.models import Avg, Count, F

from community.models import CommunityPost

from .models import MerchantStore


def get_rating_map(store_ids):
    """Return {store_id: (rata_rata, jumlah_review)} tanpa menghitung review demo."""
    owners = dict(MerchantStore.objects.filter(pk__in=store_ids).values_list('owner_id', 'pk'))
    if not owners:
        return {}
    rows = CommunityPost.objects.filter(
        post_type=CommunityPost.PostType.REVIEW,
        related_order__status='completed',
        related_order__customer_id=F('author_id'),
        related_order__surprise_bag__merchant_id__in=owners,
    ).values('related_order__surprise_bag__merchant_id').annotate(
        average=Avg('rating'), total=Count('pk'),
    )
    return {
        owners[row['related_order__surprise_bag__merchant_id']]: (round(row['average'], 1), row['total'])
        for row in rows
    }


def get_rating(store_id):
    """Return (rata_rata, jumlah_review); (None, 0) jika belum ada review terverifikasi."""
    return get_rating_map([store_id]).get(store_id, (None, 0))
