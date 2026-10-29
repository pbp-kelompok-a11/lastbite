import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from merchant_store.models import MerchantStore
from merchant_store.services import GeocodingError, geocode_address


class Command(BaseCommand):
    help = 'Mengisi koordinat (latitude/longitude) toko yang belum punya, berdasarkan alamatnya.'

    def handle(self, *args, **options):
        stores = MerchantStore.objects.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        )
        total = stores.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Semua toko sudah punya koordinat.'))
            return

        done = 0
        for index, store in enumerate(stores, start=1):
            if index > 1:
                time.sleep(1.1)  # patuhi batas 1 permintaan/detik Nominatim
            try:
                result = geocode_address(store.address)
            except GeocodingError:
                self.stdout.write(self.style.WARNING(
                    f'[{store.pk}] {store.name}: layanan peta tidak dapat dihubungi, dilewati.'
                ))
                continue

            if not result:
                self.stdout.write(self.style.WARNING(
                    f'[{store.pk}] {store.name}: alamat belum ditemukan, perpendek alamatnya lalu coba lagi.'
                ))
                continue

            store.latitude = result['lat']
            store.longitude = result['lng']
            store.save(update_fields=['latitude', 'longitude'])
            done += 1
            self.stdout.write(self.style.SUCCESS(f'[{store.pk}] {store.name}: koordinat tersimpan.'))

        self.stdout.write(f'Selesai: {done} dari {total} toko diperbarui.')