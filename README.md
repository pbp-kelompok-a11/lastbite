# LastBite

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
