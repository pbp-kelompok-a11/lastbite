# Integrasi Order, Community Review, dan Rating Toko

Basis implementasi: origin/dev 585a875, yang sudah mencakup branch Community, Merchant Store, Surprise Bag, Eco Impact, dan autentikasi. Dikerjakan di feature/order-module.

## Alur

1. Customer menyelesaikan pickup melalui modul Order yang sudah ada.
2. Pesanan Completed menampilkan Tulis Review; tautan membuka form Community dengan order tersebut sudah dipilih.
3. Pilihan hanya berisi pesanan Completed milik Customer yang belum diulas. Pengguna tetap dapat membuka URL form Community langsung dan memilih transaksi yang memenuhi syarat.
4. Form menyimpan rating dan konten secara asinkron. Judul, author, jenis postingan, dan identitas merchant berasal dari server dan relasi Order, bukan input bebas browser.
5. Setelah tersimpan, UI menampilkan Lihat Review tanpa reload. Pengiriman form tanpa JavaScript juga didukung melalui redirect biasa.
6. Pesanan yang sudah diulas menampilkan Lihat Review. Satu pesanan hanya memiliki satu review, dilindungi oleh constraint database dan lock pada order saat penyimpanan.
7. Review publik menampilkan label Pembelian terverifikasi dan nama merchant, tanpa kode pickup atau reservation key.
8. Rating Merchant Store dihitung dari review yang pemilik/penulis dan status order-nya cocok. Relasi toko mengikuti MerchantStore.owner dan SurpriseBag.merchant; tidak dibuat model atau field toko duplikat.

## Struktur

- community/models.py: FK related_order dengan PROTECT, validasi model, penanda pembelian terverifikasi, dan constraint satu review per order.
- community/forms.py: memperluas ReviewForm asli dengan queryset order milik Customer dan judul otomatis berdasarkan snapshot nama makanan.
- community/views.py: memakai function-based views, transaction.atomic, session authentication, role helpers accounts, CSRF, dan respons AJAX JsonResponse seperti pola modul teman.
- community/templates dan community/static: memperbarui template, CSS, serta script review asli. Warna, font, tombol, bintang rating, dan komponen Community tetap digunakan.
- order/views.py dan template order_cards.html: menambahkan tautan review pada order Completed; Subquery menghindari query terpisah untuk setiap kartu.
- merchant_store/ratings.py: mengisi fungsi agregasi yang sebelumnya merupakan placeholder, sehingga detail toko dan direktori memakai integrasi rating yang sama.
- community/tests.py: memperbarui fixtures/test demo menjadi order nyata dan menambahkan test integrasi keamanan dan rating.
- community/migrations/0005_communitypost_related_order_and_more.py: migration baru; migration teman sebelumnya tidak diubah.

## Data lama dan keamanan

related_order nullable untuk mempertahankan review demo yang sudah tersimpan. Tidak ada transaksi palsu yang dibuat untuk memverifikasi data lama. Review lama tanpa transaksi tetap berlabel Belum terverifikasi dan tidak masuk rata-rata rating toko. Pembuatan review baru wajib memilih order yang valid melalui form dan validasi model.

Server memeriksa role Customer, status Completed, kepemilikan, dan duplikasi. Guest memakai halaman login bersama. Merchant dan akun tanpa role tidak boleh membuat review. Status pending, ready_to_pickup, cancelled, ID order asing, ID hilang, dan ID tidak valid ditolak.

## Verifikasi

- 201 tests proyek lulus pada SQLite dan Django 5.2.18, termasuk seluruh tests autentikasi, Order, Community, dan Merchant Store.
- Django check bersih dan makemigrations --check --dry-run tidak menemukan perubahan yang belum dimigrasikan.
- Pemeriksaan sintaks JavaScript dan git diff --check lulus.
- Browser: reservasi, ready, verifikasi pickup, Completed, tautan review dengan order dipilih, submit AJAX tanpa navigasi, detail terverifikasi, filter, privasi kode, dan layout desktop/mobile lulus. Tampilan 1440 px dan 390 px diperiksa.
- Browser menggunakan bridge ke Django Test Client dengan CSRF aktif; koneksi HTTP deployment/PWS dan konkurensi PostgreSQL belum diuji.

Untuk environment lain, jalankan migration sebelum server memuat perubahan ini:

    python manage.py migrate

Untuk konfigurasi lokal yang telah disiapkan di komputer ini:

    python manage.py migrate --settings=lastbite.local_settings

Tidak ada perubahan yang dibuat pada isi review teman, Food Hack, komentar, likes, atau alur transaksi Order yang sudah ada. Perubahan ini belum di-push ke GitHub.
