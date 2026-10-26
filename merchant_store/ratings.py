"""Jembatan ke Modul Community untuk rata-rata rating toko.

Rating toko dihitung dari CommunityPost (post_type='review') milik Modul 4.
Saat file ini dibuat, model CommunityPost dan Order belum ada, sehingga
fungsi di bawah mengembalikan dict kosong (tampil "Belum ada rating").

Setelah Modul Community & Order selesai, cukup isi get_rating_map() di sini
(modul Merchant Store lainnya tidak perlu diubah). Contoh, jika Order
menyimpan relasi ke toko lewat field `store`:

    from django.db.models import Avg, Count
    from community.models import CommunityPost

    rows = (
        CommunityPost.objects
        .filter(post_type='review', related_order__store_id__in=store_ids)
        .values('related_order__store_id')
        .annotate(avg=Avg('rating'), total=Count('id'))
    )
    return {r['related_order__store_id']: (round(r['avg'], 1), r['total']) for r in rows}
"""


def get_rating_map(store_ids):
    """Return {store_id: (rata_rata, jumlah_review)} untuk store_ids yang punya review."""
    return {}


def get_rating(store_id):
    """Return (rata_rata, jumlah_review). rata_rata = None jika belum ada review."""
    return get_rating_map([store_id]).get(store_id, (None, 0))
