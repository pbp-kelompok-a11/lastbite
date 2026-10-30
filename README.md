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
    * AI Disclosure & Analisis Kritis Keterbatasan AI (Modul Eco Impact):
    Dalam pengerjaan Proyek LastBite pada Modul Eco Impact (Impact Journal & Green Wallet), saya (Khayla Syafira Ardiasih) menggunakan AI sebagai referensi teknis untuk penyusunan arsitektur logika metrik dampak lingkungan, integrasi endpoint AJAX visualisasi, pembuatan komponen dasbor interaktif, dan penulisan rangkaian unit test.

    Tools yang Digunakan: ChatGPT

    Bagian yang Dibantu AI:
    1. Menyusun struktur dasar endpoint API (`summary_api` dan `logs_api`) untuk agregasi data kalkulasi makanan terselamatkan, reduksi emisi karbon (CO2), dan penghematan biaya.
    2. Memberikan referensi template komponen UI visual dasbor (kartu metrik Jejak Baikmu, diagram batang tren bulanan, kartu status gamifikasi Waste Warrior, dan riwayat log).
    3. Menyusun kerangka awal fungsi JavaScript asinkron (`fetch`) untuk memuat data riwayat log dan memperbarui statistik tanpa memuat ulang halaman secara penuh (full page reload).
    4. Menyusun draf rangkaian unit test untuk menguji kode respon HTTP (200, 302, 400, 403, 404), validasi form, hak akses antar-peran, dan fungsi agregasi metrik.

    Analisis Kritis Keterbatasan AI & Perbaikan Manual:

    1. Integritas Data Transaksi vs Manipulasi Log (Data Tampering): AI awalnya mengizinkan seluruh log diedit melalui form yang sama. Saya menganalisis bahwa log yang bersumber dari pesanan harus bersifat imutabel sebagai bukti transaksi, sehingga saya memblokir hak edit dan hapus pada log dengan `log.source == 'order'` di `views.py` dan hanya mengizinkannya pada log penyelamatan mandiri (`source == 'manual'`).
    2. Formula Rasio Konversi Emisi Karbon (CO2): AI mengusulkan konstanta emisi global statis tanpa konteks ilmiah yang jelas. Saya mengkritisinya karena limbah makanan di Indonesia didominasi organik berkadar air tinggi. Saya menetapkan faktor emisi backend terverifikasi (1.9 kg CO2 per kg makanan) agar estimasi dampak lingkungan tidak menyesatkan (greenwashing).
    3. Celah Keamanan Insecure Direct Object References (IDOR): AI membuat endpoint edit dan hapus hanya memfilter berdasarkan `ImpactLog.objects.get(pk=id)`. Saya mengidentifikasi celah ini dan secara manual mengunci kueri dengan `user=request.user` pada `get_object_or_404` agar pengguna tidak dapat memanipulasi atau menghapus catatan dampak milik pengguna lain via modifikasi parameter URL/payload.
    4. Kalkulasi Selisih Penghematan Finansial (Quantity Multiplication): AI mengkalkulasi penghematan hanya dari selisih harga satuan `(original_price - discounted_price)`. Saya mengoreksi logika ini pada property `money_saved` di `ImpactLog` agar mengalikan selisih harga dengan `quantity` (jumlah porsi) agar nominal penghematan di dasbor tidak keliru saat penyelamatan makanan berjumlah jamak.
    5. Resolusi Relasi Kosong (Null Traversal) Nama Toko: AI hanya membaca field `notes` untuk menampilkan nama merchant pada kartu log, menyebabkan log riwayat pesanan berlabel placeholder `[Nama Toko]`. Saya merombak `logs_api` di `views.py` untuk menelusuri rantai relasi toko secara defensif menggunakan `getattr` dengan fallback bertingkat sebelum beralih ke `notes`.
    6. Celah Manipulasi Klien pada Level Gamifikasi: AI menyarankan penentuan tingkatan Waste Warrior dihitung di JavaScript frontend berdasarkan teks DOM. Saya menolak pendekatan ini karena rentan dimanipulasi melalui inspeksi elemen browser; seluruh kalkulasi progres level (Seedling Saver hingga Earth Guardian) dan target porsi saya sentralisasi di backend `summary_api`.
    7. Metode Destruktif Tanpa Proteksi CSRF: AI menghasilkan aksi penghapusan log menggunakan tag tautan `<a>` berbasis HTTP GET. Saya mengkritisi risiko penghapusan tak sengaja dan celah CSRF ini, lalu merombaknya di template menjadi form submit berproteksi token CSRF dengan konfirmasi dialog JavaScript.
    8. Kebocoran Isolasi Styling CSS (Global Scope Pollution): AI menulis aturan CSS yang menimpa tag `body` dan tipografi secara global di `eco_impact.css`, merusak tampilan navbar dan footer halaman lain. Saya membatasi cakupan (scoping) selector secara ketat ke dalam namespace kelas komponen `.eco-*`.
    9. Kerapuhan URL Routing Tombol Aksi (Error 404): AI merender tautan tombol edit pada frontend ke rute `/edit/<uuid>/`, padahal rute terdaftar di `urls.py` menggunakan prefiks `/logs/edit/<uuid>/`. Saya menambahkan URL alias `edit_log_alt` dan `delete_log_alt` pada `eco_impact/urls.py` agar aksi tombol pensil tidak menghasilkan error 404.
    10. Sanitasi Tag HTML & Penanganan XSS pada Catatan: AI berasumsi field `CharField` otomatis bebas dari celah injeksi skrip. Saya menambahkan pembersihan string `.strip()` pada backend dan pembatasan panjang karakter pada form catatan manual guna mengantisipasi eksekusi muatan skrip berbahaya saat nama toko/catatan dirender kembali di dasbor via AJAX.
    11. Pencegahan Anomali Data (Negative & Zero Values): AI membiarkan input jumlah porsi bernilai nol atau negatif lolos ke database. Saya memperbaikinya dengan menggunakan `PositiveIntegerField(default=1)` pada model `ImpactLog` serta menambahkan widget `min: 1` pada `ImpactLogForm` agar data input selalu bernilai positif valid.
    12. Efisiensi Query Agregasi (Database-Level Calculations): AI menghitung akumulasi total dampak dengan memuat seluruh objek model ke memori lalu menjalankan loop manual di Python. Saya mengoptimalkannya dengan memanfaatkan metode agregasi dan kueri langsung berbasis filter pengguna di Django ORM demi efisiensi performa server.
    13. Asumsi Keliru Dukungan Browser pada Web Share API: AI membuat tombol bagikan pencapaian langsung memanggil `navigator.share` tanpa penanganan kegagalan. Saya menambahkan blok fallback otomatis berupa penyalinan tautan ke clipboard (`navigator.clipboard.writeText`) beserta notifikasi alert agar fitur tetap berfungsi di browser desktop yang tidak mendukung Web Share.
    14. Inkonsistensi State Metrik Pasca-Input AJAX: AI menyarankan memuat ulang halaman secara penuh (full page reload) setiap kali pengguna menambah log manual. Saya menolak saran ini dan membangun alur asinkron di mana respons sukses AJAX langsung mentrigger fetch ulang `summary_api` dan `logs_api` agar kartu metrik di atasnya ter-update instan tanpa mereset posisi scroll pengguna.
    15. Query Filter Rentang Waktu Rentan Perbedaan Zona Waktu: AI memfilter data mingguan dan bulanan menggunakan manipulasi string tanggal lokal mentah. Saya memperbaikinya dengan query ORM `created_at__gte` berbasis `django.utils.timezone.now()` dan `timedelta` agar sinkron dengan konfigurasi zona waktu server.
    16. Implementasi Diagram Batang 6 Bulan Mandiri: AI mengusulkan impor pustaka charting pihak ketiga yang berat dan memperlambat first load. Saya menggantinya dengan implementasi CSS Grid Bar Chart mandiri yang menghitung rasio persentase dinamis langsung dari respons JSON backend `monthly_trend`, menjaga aplikasi tetap ringan tanpa dependensi luar.
    17. Cakupan Pengujian Keamanan & Kondisi Batas (Edge Cases): AI awalnya hanya menyusun unit test skenario ideal (happy path) dengan asumsi pengguna selalu valid. Saya memperluasnya secara manual menjadi 16 pengujian komprehensif di `eco_impact/tests.py`, mencakup proteksi akses Guest (302 redirect), penolakan akses Merchant (403 PermissionDenied), isolasi data antar-pengguna, pemblokiran edit log pesanan otomatis, dan akurasi formula matematis metrik dampak.
