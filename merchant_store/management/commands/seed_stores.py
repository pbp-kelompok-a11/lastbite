from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserProfile
from merchant_store.models import MerchantStore

# Nama toko & alamat (Contoh)
DEMO_STORES = [
    ('Bakers Corner UI', 'Jl. Margonda Raya No. 10, Pondok Cina, Depok', -6.3689, 106.8317, '06:00', '21:00'),
    ('Kafe Hijau Depok', 'Jl. Kukusan Teknik No. 5, Beji, Depok', -6.3586, 106.8236, '08:00', '22:00'),
    ('Kopiku Margonda', 'Jl. Margonda Raya No. 88, Kemiri Muka, Depok', -6.3735, 106.8333, '07:00', '23:00'),
    ('Sweet Studio', 'Jl. Akses UI No. 12, Kelapa Dua, Depok', -6.3510, 106.8350, '09:00', '20:00'),
    ('Warung Bu Tini Kutek', 'Jl. Kutek No. 3, Beji, Depok', -6.3563, 106.8310, '10:00', '21:00'),
    ('Dapur Mama Pocin', 'Jl. Pocin Raya No. 7, Pondok Cina, Depok', -6.3650, 106.8340, '09:00', '19:00'),
    ('Bento Corner Depok', 'Jl. Margonda Raya No. 150, Depok', -6.3790, 106.8330, '10:00', '22:00'),
    ('Roti Bakar Barokah', 'Jl. Raya Bogor No. 21, Beji, Depok', -6.3880, 106.8250, '16:00', '02:00'),
    ('Pastry Lab Cinere', 'Jl. Cinere Raya No. 9, Cinere, Depok', -6.3270, 106.7800, '08:00', '20:00'),
    ('Nasi Box Sawangan', 'Jl. Raya Sawangan No. 45, Sawangan, Depok', -6.4090, 106.7640, '08:00', '18:00'),
]


class Command(BaseCommand):
    help = 'Membuat data demo toko (merchant dummy tanpa password) untuk menguji direktori & radius.'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        created = 0
        for index, (name, address, lat, lng, opening, closing) in enumerate(DEMO_STORES, start=1):
            user, user_created = User.objects.get_or_create(username=f'demo_merchant_{index}')
            if user_created:
                user.set_unusable_password()
                user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': UserProfile.Role.MERCHANT})
            _, store_created = MerchantStore.objects.get_or_create(
                owner=user,
                defaults={
                    'name': name, 'address': address, 'phone': f'0812345678{index:02d}',
                    'description': 'Toko demo LastBite.',
                    'opening_time': opening, 'closing_time': closing,
                    'latitude': lat, 'longitude': lng,
                },
            )
            created += int(store_created)
        self.stdout.write(self.style.SUCCESS(f'Selesai: {created} toko demo baru ({len(DEMO_STORES)} total demo).'))
