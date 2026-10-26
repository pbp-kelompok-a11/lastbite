# Modul Order: Pemesanan dan Status Pickup

Catatan terbaru: integrasi review Community dan rating Merchant Store sudah diimplementasikan. Lihat [order-review-integration.md](order-review-integration.md) untuk hasil verifikasi dan kontrak relasi terbaru. Bagian sinkronisasi di bawah mencatat kondisi saat implementasi Order awal.

Branch: `feature/order-module`. Tidak ada push atau merge ke main.

## Basis dan keselarasan

Implementasi memakai main `9284433` dan mengintegrasikan branch asli `surprise_bag/inventory` pada commit `dd4887a`. Branch tersebut juga membawa implementasi Eco Impact melalui dev. Tidak ada duplikasi model SurpriseBag atau MerchantStore.

Pola mengikuti modul bersama: Django function-based views, URL namespace, Django forms, session authentication, CSRF, JsonResponse, native fetch/FormData, native dialog, dan templates yang extends base.html. CSS/JS Order ditempatkan dalam namespace app seperti Merchant Store. Warna, font, tombol, spacing, radius, navbar, dan footer memakai design system di static/css/base.css. Copy baru tidak memakai strip panjang.

## Pemetaan requirement

| Requirement | Implementasi |
| --- | --- |
| Create reservasi | Customer memilih SurpriseBag asli dan jumlah, server mengambil harga dan pemilik dari database |
| Read customer | /orders/ dan API daftar hanya menampilkan order milik customer |
| Read merchant | Query dibatasi melalui surprise_bag__merchant=request.user |
| Update | pending -> ready_to_pickup -> completed, hanya merchant pemilik |
| Delete/pembatalan | Customer hanya dapat membatalkan pending; status cancelled menyimpan histori dan mengembalikan stok tepat sekali |
| AJAX/modal | Filter, refresh, pembatalan, ready, dan verifikasi pickup menggunakan fetch tanpa reload |
| Verifikasi serah terima | Customer menunjukkan kode 8 karakter, merchant memasukkannya di modal; kode tidak dikirim pada daftar merchant |
| Autentikasi | Guest diarahkan ke login; akun tanpa profil dan role yang salah ditolak |
| Relasi antarmodul | Order FK ke SurpriseBag; penyelesaian mencatat ImpactLog otomatis dalam transaksi database yang sama |
| Review Community | Order.Status.COMPLETED, customer_id, dan surprise_bag tersedia untuk validasi oleh modul Community |

## File implementasi dan integrasi

- order/models.py, forms.py, services.py, views.py, urls.py, admin.py, tests.py.
- order/migrations/0001_initial.py.
- order/templates/order/list.html, form.html, components/order_cards.html.
- order/static/order/css/order.css dan js/order.js.
- main/templates/base.html: tautan Pesanan berdasarkan role.
- surprise_bag/views.py: role bersama, konteks customer, dan penonaktifan paket yang dilindungi histori Order.
- surprise_bag/templates/surprise_bag/detail.html: tombol reservasi ke Order.
- eco_impact/migrations/0001_initial.py: migration untuk model asli teman yang sebelumnya belum memiliki initial migration.
- lastbite/test_settings.py: SQLite terisolasi untuk pengujian, tanpa koneksi database deployment.
- .gitignore: dependensi dan fixture QA lokal tidak masuk Git.

Commit integrasi dependensi dipisahkan dari perubahan Order agar asal implementasi teman tetap tercatat di Git.

## Keamanan dan konsistensi transaksi

Role mengacu ke accounts.permissions dan UserProfile, sama dengan autentikasi di main. Legacy Group Merchant tidak menjadi jalan pintas untuk meningkatkan hak akun customer.

Reservasi menggunakan transaction.atomic, lock baris bag, dan conditional stock update dari SurpriseBag.reduce_stock. Reservation key mencegah retry reservasi yang sama mengurangi stok dua kali. Harga, jumlah, nama makanan, tanggal dan jam pickup disimpan sebagai snapshot. Input browser tidak dapat memilih pemilik, harga, kode pickup, atau status awal.

Mutasi status mengunci order, memvalidasi role dan ownership, dan memakai conditional update. Pembatalan hanya mengembalikan stok jika transisi pending ke cancelled berhasil. Completed dan pencatatan ImpactLog berada dalam satu transaksi; kegagalan pencatatan mengembalikan status ke ready_to_pickup. Pengulangan completion ditolak sehingga efek samping tidak dibuat lagi.

Order melindungi SurpriseBag dengan PROTECT. Endpoint penghapusan bag menonaktifkan paket yang sudah memiliki order agar inventaris tetap bisa dikelola tanpa menghapus histori. Admin Order bersifat baca saja untuk mencegah bypass alur stok dan penyelesaian.

Respons transaksi menggunakan never_cache. Semua mutasi memakai POST dengan CSRF. Template hasil AJAX tetap melalui autoescaping Django.

## Hasil verifikasi

- Seluruh 34 Django tests lulus, terdiri dari 13 tests autentikasi dan 21 tests Order.
- Django system check: tidak ada masalah.
- makemigrations --check --dry-run: tidak ada perubahan model tanpa migration.
- Pemeriksaan sintaks JavaScript dan git diff --check: lulus.
- Browser desktop 1440 px dan mobile 390 px: reservasi, privasi kode, ready modal, kode salah/benar, completion tanpa navigasi, filter, overflow mobile, dan JavaScript errors diperiksa dan lulus.
- Browser memakai request bridge ke Django Test Client dengan CSRF aktif karena server localhost tidak dapat diakses dari lingkungan ini. Ini memeriksa UI dan respons Django, bukan jaringan HTTP deployment.
- Screenshot lokal tersedia di .local-qa/. Fixture, dependensi, dan database QA tidak di-commit.
- Tests lulus pada SQLite dengan Django 5.2.17 dan 5.2.18. Lock konkurensi PostgreSQL dan deployment PWS belum diverifikasi pada PostgreSQL; tidak ada koneksi ke database deployment.

Jalankan dari environment Python yang sudah memasang requirements.txt:

    python manage.py check --settings=lastbite.test_settings
    python manage.py makemigrations --check --dry-run --settings=lastbite.test_settings
    python manage.py test --settings=lastbite.test_settings

Sebelum menjalankan aplikasi di environment tujuan, review migration lalu jalankan `python manage.py migrate` pada database yang memang dituju.

## Sinkronisasi dengan anggota lain

1. Surprise Bag: owner saat ini berupa FK langsung `merchant` ke User. Karena MerchantStore memakai satu owner per toko, pembatasan order mengikuti user pemilik paket tanpa perlu menduplikasi model toko. Jika nanti bag direlasikan langsung ke store, queryset ownership perlu disesuaikan bersama.
2. Autentikasi: akun merchant lama yang hanya punya Group Merchant perlu memperoleh UserProfile merchant melalui proses migrasi akun yang disepakati. Akun baru dari form bersama sudah memiliki profile.
3. Eco Impact: initial migration ditambahkan karena branch sumber belum memilikinya. Koordinasikan nama migration ini sebelum teman membuat initial migration berbeda. Model ImpactLog asli dipakai tanpa mengganti skemanya.
4. Community: model/view review belum tersedia pada basis branch ini. Pemilik modul harus memvalidasi related_order.customer_id == request.user.pk dan related_order.status == Order.Status.COMPLETED pada server. Modul review tidak dibuat ulang oleh Order.
5. Waktu pickup: SurpriseBag saat ini hanya menyediakan TimeField tanpa tanggal penawaran. Reservasi mengartikan jam itu sebagai pickup hari ini di Asia/Jakarta dan menolak jika jam akhir sudah lewat. Dukungan pickup hari lain atau stok per tanggal membutuhkan kesepakatan perubahan inventory.
6. Verifikasi memakai kode teks, sesuai requirement modal. Pemindaian QR tidak ditambahkan.
