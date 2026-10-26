import os
import random
from datetime import time
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.db import migrations

BAG_COUNT = 120  # ±10 halaman katalog (12 per halaman), cukup buat ngetes pagination
DUMMY_PREFIX = 'dummy_merchant_'

STORE_NAMES = [
    'Roti Senja Bakery', 'Kafe Kampus', 'Warung Bu Tini', 'Dapur Margonda', 'Manis Patisserie',
    'Kopi Kukusan', 'Bento Beji', 'Sweet Corner Depok', 'Warteg Barokah', 'Teh & Toast Kutek',
]

# nama menu per kategori — dikombinasikan dengan VARIANTS biar namanya bervariasi
MENU = {
    'bakery': ['Croissant', 'Roti Sobek', 'Donat Glaze', 'Danish Buah', 'Roti Tawar', 'Bagel', 'Cinnamon Roll', 'Pain au Chocolat'],
    'meal': ['Nasi Ayam Geprek', 'Nasi Goreng', 'Rice Bowl Teriyaki', 'Nasi Rames', 'Mie Goreng', 'Ayam Bakar', 'Nasi Uduk', 'Bento Katsu'],
    'snack': ['Risoles', 'Lumpia', 'Dimsum', 'Sandwich', 'Pastel', 'Gorengan', 'Kroket', 'Cireng'],
    'dessert': ['Brownies', 'Cheesecake', 'Puding', 'Tiramisu', 'Bolu Pandan', 'Klepon', 'Kue Lapis', 'Cupcake'],
    'beverage': ['Es Kopi Susu', 'Cold Brew', 'Es Teh Lemon', 'Jus Jeruk', 'Matcha Latte', 'Es Cokelat', 'Smoothie Mangga', 'Thai Tea'],
    'mixed': ['Paket Hemat', 'Surprise Bag', 'Paket Sore', 'Paket Kenyang', 'Mystery Box', 'Paket Sarapan', 'Paket Makan Malam', 'Bundling Akhir Hari'],
}
VARIANTS = ['Box', 'Mix', 'Duo', 'Trio', 'Spesial', 'Jumbo', 'Hemat', 'Komplit']
PRICE_RANGE = {
    'bakery': (25000, 70000),
    'meal': (20000, 60000),
    'snack': (15000, 45000),
    'dessert': (25000, 80000),
    'beverage': (15000, 50000),
    'mixed': (35000, 90000),
}
PICKUP_SLOTS = [(16, 18), (17, 19), (18, 20), (19, 21), (20, 22)]


def seed_dummy_bags(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    SurpriseBag = apps.get_model('surprise_bag', 'SurpriseBag')

    rng = random.Random(42)  # seed tetap supaya data sama di setiap database
    password = make_password(os.environ.get('SEED_MERCHANT_PASSWORD', 'dummy12345'))

    merchants = []
    for index, store in enumerate(STORE_NAMES, start=1):
        user, _ = User.objects.get_or_create(
            username=f'{DUMMY_PREFIX}{index}',
            defaults={'first_name': store, 'password': password},
        )
        # role merchant ditentukan lewat UserProfile (app accounts)
        UserProfile.objects.update_or_create(user=user, defaults={'role': 'merchant'})
        merchants.append(user)

    # jangan seed dua kali kalau merchant dummy sudah punya bag
    if SurpriseBag.objects.filter(merchant__in=merchants).exists():
        return

    bags = []
    for _ in range(BAG_COUNT):
        merchant = rng.choice(merchants)
        category = rng.choice(list(MENU))
        item = rng.choice(MENU[category])
        low, high = PRICE_RANGE[category]
        price = rng.randrange(low, high + 1, 1000)
        discount = rng.randint(30, 48)
        # bulatkan ke bawah kelipatan Rp500 (hasil tetap di rentang diskon 30–50%)
        discounted = int(price * (100 - discount) / 100) // 500 * 500
        start, end = rng.choice(PICKUP_SLOTS)
        bags.append(SurpriseBag(
            merchant=merchant,
            name=f'{item} {rng.choice(VARIANTS)}',
            description=(
                f'{item} sisa produksi hari ini dari {merchant.first_name}. '
                'Masih segar dan layak konsumsi — ambil sebelum jam tutup ya!'
            ),
            category=category,
            original_price=Decimal(price),
            discounted_price=Decimal(discounted),
            stock=0 if rng.random() < 0.15 else rng.randint(1, 20),  # ~15% sengaja habis
            pickup_start=time(start),
            pickup_end=time(end),
            is_active=rng.random() >= 0.1,  # ~10% nonaktif
        ))
    SurpriseBag.objects.bulk_create(bags)


def unseed_dummy_bags(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # bag ikut terhapus (CASCADE); akan gagal kalau bag sudah punya pesanan (Order memakai PROTECT)
    User.objects.filter(username__startswith=DUMMY_PREFIX).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('surprise_bag', '0003_surprisebag_image_url'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_dummy_bags, unseed_dummy_bags),
    ]
