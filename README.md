# LastBite

Link Figma: [LastBite](https://www.figma.com/design/zDAuPEQmxaq2GS0vTwFvXr/LastBite?node-id=0-1&t=iZNwDjawzaXseNsp-1)

## Anggota Kelompok A11
- 2506622802	SALWA ALYANI NAZNIN
- 2506656910	KHAYLA SYAFIRA ARDIASIH
- 2506656734	FATHIR ATHA RIZKI TASRIL
- 2506618723	AZZAM ZAWAWI AL RASYID
- 2506549051	GDE MAHARTA PUTRA WICAKSANA RIDJASA

## Deskripsi Aplikasi

LastBite adalah platform marketplace yang menghubungkan merchant makanan (bakery, kafe, restoran) dengan pembeli di sekitar kampus dan area kos, khusus untuk stok makanan yang mendekati jam tutup toko. Setiap hari, banyak merchant terpaksa membuang roti, nasi, dan pastry yang sebenarnya masih layak konsumsi karena tidak habis terjual. Di sisi lain, mahasiswa dan pekerja muda dengan budget terbatas sering kesulitan mendapat makanan berkualitas dengan harga terjangkau. LastBite mempertemukan kedua kebutuhan ini. Merchant memposting "surprise bag" berisi stok tersisa dengan harga diskon 30-50%, pembeli bisa menemukan deal aktif di sekitar mereka lewat peta interaktif, memesan lewat aplikasi, dan mengambilnya langsung ke toko menggunakan kode QR sebelum jam tutup. Selain menghemat pengeluaran pembeli dan menyelamatkan pemasukan merchant, setiap transaksi di LastBite turut mengurangi food waste, dampak yang dapat dilihat penggunanya lewat estimasi kilogram makanan terselamatkan dan jejak karbon yang berhasil dihindari.

* Sub-tema
    Sustainable Food & Diet, dengan elemen Waste Management di dalamnya (food waste reduction).

* Bentuk Aplikasi

    Marketplace lokal yang menghubungkan merchant (bakery/kafe/resto) yang memiliki stok makanan mendekati kedaluwarsa atau menjelang tutup toko, dengan pembeli di sekitar kampus/kos yang ingin membeli dengan harga diskon 30-50%.

* Target Pengguna & Masalah yang Diselesaikan

    Target pengguna:

    Pembeli: mahasiswa & pekerja muda dengan budget terbatas, yang ingin makan enak/hemat dan responsif terhadap deal instan.
    Merchant: bakery, kafe, warung, resto yang rutin memiliki stok makanan tersisa tiap tutup toko dan selama ini hanya dibuang.

    Masalah: 

    Setiap hari, merchant makanan (terutama bakery/kafe) membuang stok layak konsumsi karena tidak habis terjual sebelum tutup. Di sisi lain, banyak mahasiswa/pekerja muda yang budget nya ketat dan ingin membeli makanan berkualitas dengan harga lebih murah. LastBite menjembatani dua kebutuhan ini secara real time: merchant mendapat pemasukan tambahan dari stok yang harusnya rugi total, pembeli mendapat makanan enak dengan harga diskon, dan food waste berkurang sebagai dampak sampingnya.

## Jenis & Peran Pengguna (User Roles)

* Guest : Pengunjung umum yang belum login. Memiliki akses read-only (melihat katalog Surprise Bag, peta lokasi & direktori merchant, ulasan publik, serta konten tips komunitas). Tidak dapat melakukan transaksi atau membuat konten.

* Customer : Pengguna terdaftar (konsumen). Dapat memesan Surprise Bag, mengelola riwayat pesanan, menulis ulasan merchant (bersyarat transaksi selesai), membagikan tips food hack, memberikan upvote, serta memantau dampak lingkungan dan penghematan pribadi. 

* Merchant : Pengguna terdaftar (pemilik usaha F&B). Dapat mendaftarkan profil dan alamat toko, mengelola inventaris makanan surplus harian (CRUD Surprise Bag), serta memproses verifikasi dan mengubah status pesanan masuk.


## Integrasi Public API

Aplikasi LastBite terintegrasi dengan [OpenStreetMap Nominatim API](https://nominatim.org/) sebagai Public API utama platform.

Nominatim API digunakan untuk mendapatkan koordinat lokasi merchant berdasarkan alamatnya melalui fitur geocoding yang mengembalikan data dalam format JSON. Dalam LastBite, koordinat tersebut digunakan untuk menampilkan merchant pada peta interaktif sehingga pembeli dapat menemukan Surprise Bag yang tersedia di lokasi terdekat. Penggunaan API ini berkaitan langsung dengan konsep LastBite sebagai marketplace lokal yang mempertemukan merchant makanan surplus dengan pembeli di sekitar mereka.


## Daftar Modul & Pembagian Tugas Anggota

Sistem dibagi menjadi lima modul utama, masing-masing berpusat pada satu entitas data utama, dikerjakan oleh satu anggota kelompok, mencakup Models, Views, Templates, Forms, siklus CRUD lengkap, interaktivitas AJAX/HTMX, serta pembatasan akses berbasis autentikasi.

1. Modul Surprise Bag : Surplus Food Inventory
    * Penanggung Jawab: 2506549051	GDE MAHARTA PUTRA WICAKSANA RIDJASA
    * Data Utama: `SurpriseBag`
    * Deskripsi: Mengelola inventaris makanan surplus harian yang ditawarkan Merchant kepada Customer.
    * Tanggung Jawab CRUD:
        * Create: Merchant membuat penawaran Surprise Bag baru (nama paket, deskripsi, kategori, harga normal, harga diskon, kuota stok, waktu pengambilan).
        * Read: Guest dan Customer melihat etalase katalog Surprise Bag yang sedang aktif.
        * Update: Merchant mengubah harga diskon, kuota stok, dan jam pickup.
        * Delete: Merchant menghapus atau menonaktifkan penawaran Surprise Bag.
    * AJAX / HTMX & Filter: Filter katalog asinkron berdasarkan kategori makanan, rentang harga diskon, dan ketersediaan stok tanpa reload halaman penuh. Pembaruan kuota stok berjalan secara dinamis.
    * Autentikasi: Guest bersifat read-only; Customer diarahkan ke Modul Order untuk membeli; hak modifikasi data dibatasi murni untuk Merchant pemilik paket.
    * Initial Data: Bertanggung jawab atas penyediaan dan seeding minimal 50 data awal produk makanan surplus ke basis data aplikasi untuk kebutuhan deployment awal di PWS.

2. Modul Order : Pemesanan & Status Pickup
    * Penanggung Jawab: 2506622802	SALWA ALYANI NAZNIN
    * Data Utama: `Order`
    * Deskripsi: Mengelola siklus transaksi antara Customer dan Merchant sejak reservasi dibuat hingga pesanan selesai diserahterimakan.
    * Tanggung Jawab CRUD:
        * Create: Customer membuat pesanan/reservasi untuk Surprise Bag yang tersedia.
        * Read: Customer melihat riwayat transaksinya; Merchant melihat daftar pesanan masuk ke tokonya.
        * Update: Merchant memperbarui alur status transaksi (Pending → Ready to Pickup Completed).
        * Delete: Customer membatalkan pesanan yang belum diproses oleh Merchant.
    * AJAX / HTMX & Interaktivitas: Pembaruan status transaksi secara asinkron dan verifikasi serah terima makanan menggunakan modal dialog interaktif tanpa reload halaman.
    * Autentikasi: Customer hanya dapat mengakses pesanannya sendiri; Merchant hanya dapat memproses pesanan tokonya; Guest dilarang mengakses sistem transaksi.
    * Relasi Antarmodul: Mengambil data `SurpriseBag` dari Modul 1. Status pesanan Completed menjadi syarat Customer untuk menulis ulasan di Modul 4 dan memicu pencatatan dampak otomatis di Modul 5.

    ### AI Disclosure & Analisis Kritis Keterbatasan AI

    **Modul Order: Pemesanan & Status Pickup**

    **Penanggung jawab: Salwa Alyani Naznin (2506622802)**

    Dalam pengerjaan Modul Order pada Proyek LastBite, saya menggunakan AI untuk membantu membaca struktur repository kelompok, merancang alur reservasi dan status pickup, menghasilkan serta merevisi kode backend, menyusun interaksi AJAX/modal, mengintegrasikan antarmodul, menyesuaikan tampilan dengan Figma, dan membuat pengujian. Bantuan AI mencakup penulisan kode implementasi, bukan hanya pemberian referensi atau ide. Saya tetap bertanggung jawab untuk memahami kode, meninjau kesesuaian fitur dengan requirement, dan menjelaskan keputusan teknis modul yang saya kerjakan.

    **Tools yang Digunakan:** ChatGPT melalui Codex, termasuk integrasi Figma untuk membaca konteks desain dan aset yang menjadi acuan implementasi antarmuka.

    **Strategi Penggunaan AI:** Permintaan diberikan bertahap: mempelajari modul anggota lain terlebih dahulu, memakai model `SurpriseBag` asli tanpa menduplikasinya, mengikuti autentikasi bersama, mengimplementasikan transaksi dan pembatasan akses, menyambungkan review dan Eco Impact setelah dependensinya tersedia, kemudian menyesuaikan desain dan menjalankan pengujian. Hasil AI diperiksa melalui pembacaan kode, Django checks, pengujian otomatis, dan pemeriksaan antarmuka. Pengujian dan revisi kode tersebut juga mendapat bantuan AI.

    **Bagian yang Dibantu AI:**

    1. Menyusun model `Order`, migration, form reservasi, form verifikasi pickup, URL, dan views dengan pola Django yang mengikuti repository kelompok.
    2. Mengimplementasikan `reserve_bag()` dan `transition_order()` pada `services.py`, termasuk validasi role, kepemilikan, jumlah paket, stok, waktu pickup, dan urutan perubahan status.
    3. Menambahkan transaksi atomik, penguncian baris, pengurangan/pengembalian stok, dan `reservation_key` untuk menangani pengiriman ulang reservasi yang sama.
    4. Membuat halaman reservasi, tab Aktif/Riwayat, kartu progres pesanan, modal kode pickup, serta fungsi JavaScript `fetch` untuk filter dan perubahan status tanpa memuat ulang seluruh halaman.
    5. Menghubungkan Order Completed dengan pencatatan `ImpactLog` otomatis dan review Community melalui `related_order`, termasuk tautan Tulis Review/Lihat Review serta agregasi rating Merchant Store.
    6. Mengadaptasi desain Figma menjadi Django templates dan CSS dengan komponen, token warna, font, navbar, dan footer bersama yang telah digunakan anggota kelompok lain.
    7. Menulis dan memperbarui tests untuk reservasi, stok, snapshot harga, pembatalan, perubahan status, kode pickup, CSRF, isolasi akses antar-pengguna, integrasi review, dan rollback jika proses gagal.
    8. Membantu menjelaskan alur kode, menyiapkan konfigurasi database lokal terpisah dari deployment, memeriksa migration, dan mengelola integrasi perubahan melalui branch Git.

    #### Analisis Kritis Keterbatasan AI & Penyesuaian Implementasi

    1. **Asumsi Skema Antarmodul:** AI tidak dapat menentukan relasi yang benar hanya dari deskripsi requirement. Pada pemeriksaan awal, model Surprise Bag dan Merchant Store di `main` masih berupa scaffold. Implementasi menunggu kode asli tersedia pada branch teman, lalu menggunakan FK ke `SurpriseBag` dan kepemilikan melalui `SurpriseBag.merchant`, bukan membuat model inventaris atau toko pengganti.

    2. **Inkonsistensi Representasi Role:** Modul inventaris semula memeriksa Group `Merchant`, sedangkan autentikasi bersama menggunakan `UserProfile`. Pemeriksaan akses diselaraskan dengan `accounts.permissions.is_customer` dan `is_merchant`. Keanggotaan Group saja tidak dijadikan jalan pintas untuk memperoleh hak Merchant apabila role profil tidak sesuai.

    3. **Konsistensi Stok dan Race Condition:** Pemisahan operasi membaca stok, menguranginya, dan membuat Order dapat menimbulkan data tidak konsisten. Reservasi ditempatkan dalam `transaction.atomic`, memakai `select_for_update()`, dan memanggil pengurangan stok bersyarat pada model Surprise Bag. Namun, keberhasilan tests SQLite tidak membuktikan perilaku penguncian PostgreSQL; pengujian konkurensi pada database deployment tetap merupakan verifikasi terpisah.

    4. **Pengiriman Ulang Reservasi:** Menonaktifkan tombol di browser belum cukup untuk mencegah request berulang. `reservation_key` yang unik digunakan untuk mengambil kembali Order yang sudah dibuat. Customer, paket, dan jumlahnya dicocokkan sebelum hasil lama dikembalikan. Perlindungan ini berlaku untuk key yang sama, bukan melarang Customer membuat reservasi berbeda dengan key baru.

    5. **Snapshot Harga dan Penghematan:** Harga katalog dapat berubah setelah reservasi. Order menyimpan harga normal, harga diskon, nama makanan, dan jadwal pickup saat transaksi dibuat. `total_price` dan `money_saved` dihitung dari snapshot tersebut dengan memperhitungkan `quantity`, sehingga perubahan harga paket tidak mengubah histori transaksi lama.

    6. **Pembatalan dan Riwayat Transaksi:** Requirement Delete diterapkan sebagai pembatalan berstatus `Cancelled`, bukan menghapus bukti transaksi. Customer hanya boleh membatalkan Order Pending, dan stok dikembalikan setelah transisi berhasil. FK `PROTECT` menjaga paket yang telah memiliki Order; endpoint penghapusan paket menonaktifkan penawaran tersebut agar riwayat tetap tersedia.

    7. **Otorisasi Objek dan Manipulasi Request:** UUID, field tersembunyi, dan tombol yang tidak ditampilkan bukan pengganti pemeriksaan akses. Query Customer dibatasi dengan `customer=request.user`, sedangkan Merchant dibatasi melalui pemilik Surprise Bag. Harga, identitas Customer, dan status awal ditentukan server. Mutasi memakai POST dan CSRF agar aturan tidak bergantung pada JavaScript atau input browser.

    8. **Validasi Status dan Verifikasi Pickup:** Form hanya memeriksa format kode dan menormalkan huruf melalui `clean_pickup_code()`. Kecocokan kode, kepemilikan Merchant, dan status awal diperiksa kembali di service. Alur yang diizinkan adalah Pending ke Ready to Pickup lalu Completed; lompatan dan pengulangan transisi ditolak. Kode hanya diberikan pada tampilan Customer, bukan daftar Merchant.

    9. **Efek Samping Completion dan Klaim Idempotensi:** Perubahan status Completed dan pencatatan ImpactLog dilakukan dalam transaksi yang sama agar kegagalan pencatatan membatalkan perubahan status. Pencegahan completion berulang bertumpu pada lock dan aturan transisi Order. `get_or_create()` tidak dianggap sebagai jaminan universal bebas duplikasi tanpa memperhatikan constraint database dan jalur penulisan data lainnya.

    10. **Review Demo vs Pembelian Terverifikasi:** Implementasi awal Community belum memiliki relasi transaksi. Integrasi menambahkan `related_order`, pilihan Order Completed milik Customer, validasi kepemilikan, dan constraint satu review per Order. Review contoh lama tidak diberi transaksi palsu: tetap belum terverifikasi dan tidak dihitung dalam rating toko. Identitas Merchant ditelusuri dari relasi Order, bukan dipilih bebas dari browser.

    11. **Batas Kepercayaan pada Frontend:** Preview total reservasi, label status, dan tampilan progres membantu interaksi, tetapi bukan sumber kebenaran transaksi. Server tetap memvalidasi stok, jumlah, harga, role, dan status. Respons AJAX dirender menggunakan autoescaping template, sedangkan pesan dan kode dinamis dimasukkan melalui `textContent` pada bagian antarmuka yang relevan.

    12. **Keselarasan Desain dan Efisiensi Query:** Kode contoh dari konteks Figma tidak langsung dipakai sebagai React/Tailwind karena project menggunakan Django. Implementasi diadaptasi ke template dan CSS scoped modul Order dengan komponen `lb-*` bersama; ikon disimpan lokal agar tidak bergantung pada URL aset Figma sementara. `select_related()` dan `Subquery` digunakan untuk mengambil relasi dan ID review tanpa query tambahan untuk setiap kartu.

    13. **Asumsi Waktu dan Cakupan Fitur:** Model Surprise Bag menyediakan jam pickup tanpa tanggal penawaran. Reservasi mengartikannya sebagai pickup hari ini menggunakan zona waktu aplikasi dan menolak pemesanan setelah jam akhir. Belum ada kedaluwarsa otomatis Order Pending, pembayaran, atau pemindaian QR. Completed berarti serah terima berhasil diverifikasi, bukan bukti pembayaran.

    14. **Batas Pengujian dan Atribusi Perbaikan:** Tests mencakup skenario berhasil maupun gagal, antara lain stok tidak cukup, request berulang, akses milik pengguna lain, kode salah, rollback, serta review tidak sah. Pemeriksaan browser juga dilakukan memakai database fixture terisolasi dan Django Test Client sebagai penghubung request. Hasil ini tidak disamakan dengan pengujian HTTP deployment PWS atau konkurensi PostgreSQL. Revisi implementasi dan pengujian di atas juga dibantu AI; disclosure ini tidak mengklaim seluruh perbaikan sebagai pekerjaan manual tanpa bantuan AI.

3. Modul Merchant Store : Direktori Toko & Integrasi Public API
    * Penanggung Jawab: 2506656734	FATHIR ATHA RIZKI TASRIL
    * Data Utama:`MerchantStore`
    * Deskripsi: Mengelola profil fisik toko mitra sekaligus menyediakan direktori pencarian toko berbasis peta interaktif dan radius lokasi.
    * Tanggung Jawab CRUD:
        * Create: Merchant mendaftarkan profil toko (nama gerai, alamat lengkap, kontak bisnis, jam operasional).
        * Read: Guest dan Customer melihat direktori toko, detail kontak, peta lokasi, dan rata-rata rating.
        * Update: Merchant memutakhirkan alamat, jam operasional, dan kontak bisnis tokonya.
        * Delete: Merchant menghapus atau menonaktifkan profil tokonya.
    * Integrasi Public API & Filter Data API: Menghubungkan alamat merchant ke OpenStreetMap Nominatim API untuk mendapatkan koordinat (latitude dan longitude). Melakukan pencarian toko secara asinkron serta penyaringan hasil data API berdasarkan radius jarak (misal: 1 km, 3 km, 5 km) tanpa reload halaman penuh.
    * Autentikasi: Hak kelola data profil toko hanya milik Merchant bersangkutan; Guest dan Customer hanya memiliki hak baca.
    * Fitur Pendukung: Pengelolaan relasi daftar toko favorit (*Wishlist*) oleh Customer.

4. Modul Community : Review & Food Hack
    * Penanggung Jawab: 2506618723	AZZAM ZAWAWI AL RASYID
    * Data Utama: `CommunityPost`
    * Deskripsi: Menampung seluruh kontribusi konten komunitas (ulasan merchant dan artikel tips penanganan makanan surplus) dalam satu skema basis data terpadu menggunakan pembeda `post_type` (`review` atau `food_hack`).
    * Struktur Skema Model:
        * `author` → FK ke User
        * `post_type` → CharField pilihan (`"review"` / `"food_hack"`)
        * `related_order` → FK ke Order (wajib diisi jika `post_type = review`)
        * `rating` → Integer 1–5 (khusus ulasan merchant)
        * `title`, `content`, `created_at`, `updated_at` → Metadata teks konten
    * Tanggung Jawab CRUD:
        * Create: Customer membuat ulasan toko (wajib memiliki transaksi berstatus Completed) atau menulis kiat pemanfaatan makanan (food hack tanpa syarat order).
        * Read: Guest dan Customer membaca ulasan pada profil toko serta artikel tips pada ruang komunitas.
        * Update: Customer mengedit ulasan atau artikel tips miliknya sendiri.
        * Delete: Customer menghapus ulasan atau artikel tips miliknya sendiri.
    * AJAX / HTMX & Interaktivitas: Pengiriman formulir ulasan/tips secara asinkron dan tombol apresiasi (*upvote counter*) pada artikel tips tanpa reload halaman.
    * Autentikasi: Guest bersifat read-only; pembuatan dan edit konten dibatasi untuk Customer terdaftar; penulisan review divalidasi ketat terhadap kepemilikan transaksi selesai.
    * Relasi Antarmodul: Agregasi nilai rating dari entitas review diteruskan ke Modul 3 untuk menampilkan rata-rata rating bintang pada profil toko.

5. Modul Eco Impact : Impact Journal & Green Wallet
    * Penanggung Jawab: 2506656910	KHAYLA SYAFIRA ARDIASIH
    * Data Utama: `ImpactLog`
    * Deskripsi: Mencatat, mengkalkulasi, dan menampilkan dampak ekonomi serta reduksi emisi karbon yang dihasilkan Customer dari aktivitas penyelamatan makanan.
    * Tanggung Jawab CRUD:
        * Create: Sistem mencatat log otomatis saat pesanan Modul 2 berstatus Completed; Customer dapat menambahkan catatan log manual untuk penyelamatan makanan secara mandiri.
        * Read: Customer memantau riwayat penghematan belanja dan estimasi reduksi emisi karbon (kg CO2) lewat dasbor visual personal.
        * Update: Customer mengubah parameter catatan dampak manual miliknya.
        * Delete: Customer menghapus arsip catatan dampak manual miliknya.
    * Kalkulasi Metrik (Logika Internal):
        * Menghitung total uang yang dihemat (Harga Normal - Harga Diskon).
        * Mengestimasi emisi karbon yang dicegah menggunakan formula faktor emisi lokal di level backend.
    * AJAX / HTMX & Filter: Dasbor diperbarui secara asinkron dan riwayat catatan dapat difilter berdasarkan rentang waktu (mingguan/bulanan) tanpa reload penuh.
    * Autentikasi: Seluruh data catatan dan ringkasan metrik bersifat privat, hanya dapat diakses oleh Customer pemilik akun yang bersangkutan.
    * Relasi Antarmodul: Menarik kuantitas dan harga dari transaksi `Order` yang berstatus Completed pada Modul 2.
