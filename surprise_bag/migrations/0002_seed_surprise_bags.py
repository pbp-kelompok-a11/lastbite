import os
import random
from datetime import time
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.db import migrations

# 5 merchant dummy x 10 paket = 50 data awal
MERCHANTS = [
    ('merchant_roti_senja', 'Roti Senja Bakery', [
        ('Paket Roti Manis Sore', 'bakery', 45000),
        ('Croissant Butter Box', 'bakery', 60000),
        ('Roti Tawar Gandum Utuh', 'bakery', 30000),
        ('Donat Glaze Mix (6 pcs)', 'bakery', 42000),
        ('Pastry Savory Bag', 'bakery', 55000),
        ('Bolu Pandan Potong', 'dessert', 35000),
        ('Roti Sobek Cokelat Keju', 'bakery', 38000),
        ('Danish Buah Campur', 'bakery', 50000),
        ('Paket Sarapan Roti + Susu', 'mixed', 40000),
        ('Surprise Bag Bakery Harian', 'bakery', 50000),
    ]),
    ('merchant_kafe_kampus', 'Kafe Kampus', [
        ('Paket Sandwich Kafe', 'snack', 48000),
        ('Cookies Jar Mix', 'snack', 36000),
        ('Brownies Fudge Box', 'dessert', 45000),
        ('Es Kopi Susu Botol (2 btl)', 'beverage', 44000),
        ('Cold Brew Literan', 'beverage', 70000),
        ('Muffin Blueberry Trio', 'dessert', 39000),
        ('Banana Bread Slice Pack', 'dessert', 34000),
        ('Paket Ngopi Sore', 'mixed', 52000),
        ('Pasta Salad Cup', 'meal', 40000),
        ('Surprise Bag Kafe Kampus', 'mixed', 55000),
    ]),
    ('merchant_warung_bu_tini', 'Warung Bu Tini', [
        ('Nasi Ayam Bakar Bungkus', 'meal', 28000),
        ('Nasi Rames Komplit', 'meal', 25000),
        ('Paket Lauk Rumahan (3 macam)', 'meal', 35000),
        ('Sayur Lodeh + Tempe Orek', 'meal', 22000),
        ('Nasi Uduk Telur Balado', 'meal', 20000),
        ('Gorengan Mix (10 pcs)', 'snack', 20000),
        ('Rendang Porsi Keluarga', 'meal', 60000),
        ('Pepes Ikan + Nasi', 'meal', 30000),
        ('Es Teh Manis Jumbo (3 gelas)', 'beverage', 18000),
        ('Surprise Bag Warung Bu Tini', 'mixed', 40000),
    ]),
    ('merchant_dapur_margonda', 'Dapur Margonda', [
        ('Rice Bowl Chicken Teriyaki', 'meal', 35000),
        ('Rice Bowl Beef Blackpepper', 'meal', 42000),
        ('Mie Goreng Spesial', 'meal', 30000),
        ('Dimsum Kukus Mix (8 pcs)', 'snack', 38000),
        ('Nasi Goreng Kampung', 'meal', 28000),
        ('Chicken Katsu Bento', 'meal', 40000),
        ('Lumpia Semarang (5 pcs)', 'snack', 32000),
        ('Salad Buah Segar', 'dessert', 25000),
        ('Paket Makan Siang Hemat', 'mixed', 45000),
        ('Surprise Bag Dapur Margonda', 'mixed', 50000),
    ]),
    ('merchant_manis_patisserie', 'Manis Patisserie', [
        ('Slice Cake Assorted (3 pcs)', 'dessert', 75000),
        ('Cheesecake Mini Box', 'dessert', 68000),
        ('Macaron Pastel (6 pcs)', 'dessert', 60000),
        ('Tiramisu Cup Duo', 'dessert', 54000),
        ('Eclair Cokelat Vanilla', 'bakery', 48000),
        ('Pie Buah Mini (4 pcs)', 'bakery', 52000),
        ('Puding Susu Karamel', 'dessert', 30000),
        ('Es Cokelat Premium', 'beverage', 32000),
        ('Kue Lapis Legit Potong', 'dessert', 65000),
        ('Surprise Bag Patisserie', 'mixed', 80000),
    ]),
]

PICKUP_SLOTS = [(17, 19), (18, 20), (19, 21), (20, 22)]


def seed_bags(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    SurpriseBag = apps.get_model('surprise_bag', 'SurpriseBag')

    rng = random.Random(42)  # seed tetap supaya data sama di tiap deploy
    merchant_group, _ = Group.objects.get_or_create(name='Merchant')
    password = make_password(os.environ.get('SEED_MERCHANT_PASSWORD', 'lastbite123'))

    for username, store_name, items in MERCHANTS:
        merchant, _ = User.objects.get_or_create(
            username=username,
            defaults={'first_name': store_name, 'password': password},
        )
        merchant.groups.add(merchant_group)

        for index, (name, category, price) in enumerate(items):
            discount = rng.randint(30, 48)
            # bulatkan ke bawah kelipatan Rp500 biar harganya realistis (hasil tetap 30–50%)
            discounted = int(price * (100 - discount) / 100) // 500 * 500
            start, end = rng.choice(PICKUP_SLOTS)
            SurpriseBag.objects.get_or_create(
                merchant=merchant,
                name=name,
                defaults={
                    'description': (
                        f'{name} dari {store_name}. Sisa produksi hari ini yang masih segar '
                        'dan layak konsumsi — ambil sebelum jam tutup ya!'
                    ),
                    'category': category,
                    'original_price': Decimal(price),
                    'discounted_price': Decimal(discounted),
                    # satu paket per merchant sengaja habis, buat ngetes filter stok
                    'stock': 0 if index == 7 else rng.randint(1, 15),
                    'pickup_start': time(start),
                    'pickup_end': time(end),
                },
            )


def unseed_bags(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # bag ikut terhapus karena on_delete=CASCADE
    User.objects.filter(username__in=[m[0] for m in MERCHANTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('surprise_bag', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(seed_bags, unseed_bags),
    ]
