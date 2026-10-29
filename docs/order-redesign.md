# Redesign Order LastBite

## Acuan dan struktur

- Figma: https://www.figma.com/design/zDAuPEQmxaq2GS0vTwFvXr/LastBite?node-id=1-465
- Frame: Desain Pesanan LastBite, 1280 x 1687.
- Basis repo: origin/dev aeeb065, mencakup redesign landing page, katalog Surprise Bag, Merchant Store, dan pembaruan Community.
- Menggunakan Django templates, function-based views, fetch/FormData, native dialog, dan static assets dalam namespace order.
- Memakai base.html dan komponen bersama lb-container, lb-eyebrow, lb-section-title, lb-section-sub, serta lb-btn. Warna dan font mengikuti token lb-* dari navbar_lb.css dan lb_shared.css, sama dengan modul teman.

## Perubahan

1. Halaman Customer mengikuti judul My Order, kartu progres tiga tahap, tab Aktif/Riwayat, kartu Pending ringkas yang dapat dibuka, serta tombol Tampilkan kode pickup.
2. Halaman Merchant menggunakan layout dan komponen yang sama dengan aksi Siap Diambil dan Verifikasi Pickup.
3. Tab Aktif berisi Pending dan Ready to Pickup. Riwayat berisi Completed dan Cancelled. Ready to Pickup diprioritaskan pada daftar aktif.
4. Jumlah pesanan pada tab dihitung dari queryset yang sudah dibatasi kepemilikannya. Perubahan tab, filter, refresh, serta aksi transaksi memperbarui daftar tanpa reload halaman.
5. Parameter status lama tetap didukung. Tautan dengan status completed/cancelled tanpa parameter tab otomatis membuka Riwayat.
6. Kode pickup tampil melalui dialog khusus Customer. Kode tidak dikirim pada daftar Merchant. Tanpa JavaScript, kode tetap tersedia bagi Customer melalui noscript.
7. Riwayat Completed tetap memiliki tautan Tulis Review atau Lihat Review sesuai data Community.
8. Halaman reservasi menggunakan font, kartu, warna, dan tombol baru, dilengkapi preview total berdasarkan jumlah paket. Harga akhir tetap dihitung dan divalidasi di server.
9. Foto makanan berasal dari SurpriseBag.image_url secara dinamis. Jika tidak ada atau gagal dimuat, slot gambar menggunakan emoji kategori asli dari model.

## Assets dan cakupan

Ikon clock.svg, location.svg, dan check.svg diambil dari aset asli get_design_context Figma dan disimpan di order/static/order/img/. Ukuran root 20x20, 20x20, dan 14x14 dipertahankan pada hasil browser.

Navbar, join section, dan footer memakai implementasi bersama dari dev terbaru. Perbedaan tombol akun dibanding mockup Guest mengikuti kondisi autentikasi asli aplikasi. Tidak ada perubahan pada komponen global tersebut.

Tidak ada perubahan aturan transaksi atau migration baru untuk redesign ini. Perubahan lokal pengguna pada order/forms.py, models.py, services.py, dan local_settings.py dipertahankan serta tidak dimasukkan ke commit redesign.

## Verifikasi

- 230 tests proyek lulus pada Django 5.2.18 dan SQLite.
- Django check: tidak ada masalah.
- makemigrations --check --dry-run: tidak ada perubahan yang memerlukan migration.
- Pemeriksaan sintaks JavaScript dan git diff --check lulus.
- Test tambahan mencakup pemisahan tab dan jumlah sesuai pemilik, prioritas Ready to Pickup, deep link status, serta privasi kode pada tampilan Merchant.
- Test review disesuaikan untuk mengambil pesanan Completed dari tab Riwayat.
- Uji browser pada desktop 1280 px dan mobile 390 px: tab/jumlah, popup kode, penutupan Escape, privasi Merchant, penolakan kode salah, penyelesaian pickup, review, pembatalan, filter Riwayat, total reservasi, dan pembuatan reservasi berhasil. Tidak ada overflow horizontal atau JavaScript error.
- Ikon diperiksa berdasarkan file lokal, callsite, natural dimensions, dan rendered dimensions. Font DM Serif Display dan Plus Jakarta Sans dimuat saat visual QA.
- Browser QA menggunakan database fixture terisolasi dan bridge ke Django Test Client dengan CSRF aktif. Konkurensi PostgreSQL, jaringan HTTP deployment, dan PWS tidak diuji ulang.

Screenshot QA berada di .local-qa/order-redesign-desktop.png, order-redesign-mobile.png, order-pickup-modal.png, order-pickup-mobile.png, order-reservation-desktop.png, order-reservation-mobile.png, order-history-desktop.png, dan order-merchant-desktop.png. Artefak QA dan font cache tidak dimasukkan ke Git.

Implementasi disimpan pada branch feature/order-module. Belum di-push atau digabungkan ke dev/main.
