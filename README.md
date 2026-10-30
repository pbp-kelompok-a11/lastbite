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

    # AI Disclosure & Analisis Kritis Keterbatasan AI

    Dalam pengerjaan Proyek LastBite pada Modul Surprise Bag, saya menggunakan AI sebagai asisten teknis untuk membantu memahami struktur aplikasi Django, merancang alur pengelolaan paket makanan surplus, menyusun logika katalog dan inventaris merchant, mengembangkan fitur wishlist, serta mengevaluasi validasi data dan pengujian fungsional. Saya memanfaatkan **Claude Sonnet 5.5 dan Claude Opus 5.5** sebagai alat bantu selama proses pengembangan, terutama untuk mengeksplorasi alternatif implementasi, meninjau logika program, dan mengidentifikasi potensi kesalahan pada integrasi antarkomponen.

    **Tools yang Digunakan:** Claude Sonnet 5.5 dan Claude Opus 5.5

    ### Bagian yang Dibantu AI

    1. **Perancangan Struktur Model Surprise Bag:** Membantu mengevaluasi struktur model `SurpriseBag` yang menyimpan informasi paket makanan, merchant pemilik, kategori, harga normal, harga diskon, stok, foto, serta rentang waktu pengambilan (*pickup*).

    2. **Pengembangan Logika Katalog Paket Makanan:** Memberikan referensi implementasi halaman katalog yang menampilkan paket makanan aktif, menyediakan informasi harga dan ketersediaan stok, serta mendukung navigasi ke halaman detail paket.

    3. **Implementasi Pencarian dan Filter Katalog:** Membantu merancang logika pencarian berdasarkan nama dan deskripsi, penyaringan berdasarkan kategori dan rentang harga, serta penanganan parameter pencarian yang tidak valid.

    4. **Pengurutan dan Paginasi Katalog:** Membantu mengevaluasi pilihan pengurutan berdasarkan paket terbaru, harga termurah, harga termahal, besarnya diskon, dan jarak merchant. AI juga digunakan sebagai referensi dalam merancang paginasi agar katalog tetap mudah dinavigasi ketika jumlah paket meningkat.

    5. **Validasi Harga dan Persentase Diskon:** Membantu menyusun aturan validasi harga jual agar lebih rendah daripada harga normal, termasuk penerapan rentang diskon 30–50% sesuai konsep bisnis LastBite.

    6. **Pengembangan CRUD Paket untuk Merchant:** Memberikan referensi implementasi fungsi pembuatan, pengubahan, dan penghapusan paket makanan, termasuk pemisahan hak akses antara merchant dan customer.

    7. **Pengelolaan Stok dan Status Paket:** Membantu mengevaluasi logika pembaruan stok serta status aktif paket agar merchant dapat mengelola penawaran tanpa harus menghapus seluruh data paket ketika penawaran tidak lagi tersedia.

    8. **Pengembangan Endpoint AJAX:** Membantu menyusun pendekatan endpoint API untuk mengambil data katalog dalam format JSON, memperbarui stok, dan mengubah status aktif paket tanpa selalu bergantung pada pemuatan ulang halaman secara penuh.

    9. **Integrasi Informasi Merchant Store:** Memberikan referensi untuk menghubungkan data paket dengan identitas toko merchant, termasuk penanganan kondisi ketika informasi toko belum tersedia dan aplikasi perlu menggunakan nama akun sebagai alternatif.

    10. **Perhitungan Jarak Paket dari Lokasi Customer:** Membantu mengevaluasi pendekatan perhitungan jarak menggunakan rumus Haversine, pemrosesan koordinat latitude dan longitude, serta pengurutan paket berdasarkan jarak ketika informasi lokasi pengguna tersedia.

    11. **Implementasi Fitur Wishlist:** Membantu merancang relasi `BagWishlist` antara customer dan paket makanan, termasuk mekanisme menambahkan atau menghapus paket dari daftar favorit serta menampilkan status favorit pada katalog dan halaman detail.

    12. **Penanganan Foto Paket Makanan:** Memberikan referensi untuk pengelolaan unggahan foto, penggunaan URL gambar alternatif, dan penanganan batas ukuran file agar merchant dapat menampilkan representasi visual paket makanan.

    13. **Penanganan Kondisi Khusus dan Pesan Kesalahan:** Membantu mengevaluasi skenario seperti paket tidak ditemukan, paket nonaktif yang diakses pengguna lain, stok tidak mencukupi, parameter filter tidak valid, dan permintaan API dengan format data yang salah.

    14. **Penyusunan Unit Test:** Membantu mengembangkan ide pengujian untuk model, form, hak akses, operasi CRUD, endpoint AJAX, filter katalog, paginasi, pengurutan berdasarkan jarak, wishlist, serta data awal paket makanan.

    ### Analisis Kritis Keterbatasan AI & Perbaikan Manual

    1. **Validasi Diskon pada Form Pembuatan dan Pembaruan:** Validasi harga tidak cukup dilakukan dengan memastikan harga diskon lebih rendah daripada harga normal. Paket dengan diskon yang terlalu kecil atau terlalu besar tetap dapat melanggar ketentuan bisnis. Saya memastikan validasi mencakup rentang diskon 30–50% dan tetap berfungsi pada `SurpriseBagUpdateForm`, meskipun harga normal tidak ditampilkan sebagai field yang dapat diubah pada form tersebut.

    2. **Konsistensi Validasi antara Form dan Model:** Validasi yang hanya ditempatkan pada antarmuka pengguna dapat dilewati ketika objek dibuat melalui jalur lain. Saya mengevaluasi pembagian tanggung jawab antara validasi pada `DiscountRangeMixin`, `SurpriseBagForm`, dan metode `clean()` pada model. Validasi form menangani aturan diskon bisnis, sedangkan model memeriksa konsistensi harga dan rentang waktu pengambilan. Pendekatan ini membantu mencegah ketergantungan berlebihan pada satu lapisan validasi.

    3. **Pencegahan Manipulasi Harga dan Stok oleh Customer:** AI dapat menghasilkan alur CRUD yang berfungsi secara teknis, tetapi belum tentu memperhitungkan pemisahan kewenangan pengguna. Saya memastikan operasi pengelolaan paket dibatasi pada merchant dan bahwa form pembaruan hanya menyediakan field yang diizinkan, yaitu foto, harga diskon, stok, jam pengambilan, dan status aktif. Dengan demikian, pengguna tidak seharusnya dapat mengubah harga normal atau identitas pemilik melalui manipulasi field pada request.

    4. **Celah Akses Antar-Merchant (IDOR):** Mengetahui UUID sebuah paket tidak boleh memberikan kewenangan untuk mengubah atau menghapus paket tersebut. Saya meninjau operasi edit, hapus, pembaruan stok, dan perubahan status agar objek terlebih dahulu dibatasi berdasarkan merchant pemilik. Pengujian juga mencakup upaya merchant lain untuk mengakses atau memodifikasi paket yang bukan miliknya, sehingga perlindungan tidak hanya bergantung pada tombol yang ditampilkan di frontend.

    5. **Penghapusan Paket yang Telah Memiliki Pesanan:** Menghapus paket secara permanen dapat menimbulkan masalah apabila paket tersebut telah direferensikan oleh data transaksi. Saya mempertimbangkan integritas relasi dengan modul Order dan memastikan penghapusan ditangani secara berbeda ketika terdapat pesanan terkait. Pada kondisi tersebut, paket dinonaktifkan alih-alih dihapus, sehingga riwayat transaksi tetap dapat dipertahankan.

    6. **Risiko Race Condition pada Pengurangan Stok:** Pemeriksaan stok yang hanya dilakukan dengan membaca nilai saat ini, kemudian menguranginya secara terpisah, dapat menyebabkan stok menjadi tidak konsisten ketika beberapa pesanan diproses hampir bersamaan. Saya menggunakan pendekatan pembaruan bersyarat melalui Django ORM, yaitu `filter(pk=self.pk, is_active=True, stock__gte=quantity).update(stock=F('stock') - quantity)`. Dengan demikian, stok hanya dikurangi apabila paket masih aktif dan jumlah yang tersedia mencukupi pada saat operasi pembaruan dilakukan.

    7. **Paket Nonaktif dan Paket Kehabisan Stok:** AI dapat menyederhanakan ketersediaan paket menjadi satu indikator yang tidak mempertimbangkan seluruh kondisi bisnis. Saya membedakan status aktif dari ketersediaan stok melalui properti `is_available`, yang mensyaratkan paket aktif dan stok lebih dari nol. Saya juga meninjau agar paket nonaktif tidak muncul dalam katalog publik, tetapi tetap dapat diakses pemiliknya untuk keperluan pengelolaan.

    8. **Penanganan Koordinat Lokasi yang Tidak Valid:** Fitur pengurutan berdasarkan jarak bergantung pada koordinat yang berasal dari browser dan tidak selalu dapat dipercaya. Saya mengevaluasi validasi latitude dan longitude agar hanya menerima nilai numerik yang berada dalam rentang geografis yang sah serta bukan nilai tak hingga atau `NaN`. Jika lokasi tidak tersedia atau tidak valid, katalog tetap harus dapat digunakan tanpa memaksakan pengurutan jarak yang keliru.

    9. **Akurasi Pengurutan Berdasarkan Jarak:** Mengurutkan paket berdasarkan kedekatan merchant membutuhkan perhitungan jarak yang konsisten, bukan sekadar membandingkan angka latitude dan longitude. Saya menggunakan rumus Haversine untuk memperkirakan jarak garis lurus antara lokasi customer dan toko merchant. Saya juga mempertimbangkan merchant yang belum memiliki koordinat agar tidak menyebabkan kegagalan proses pengurutan dan ditempatkan setelah paket yang jaraknya dapat dihitung.

    10. **Ketergantungan pada Relasi Merchant Store:** Informasi nama toko tidak selalu tersedia karena data merchant store dapat belum dibuat. Saya meninjau penggunaan relasi `merchant_store` agar aplikasi tidak langsung menghasilkan error ketika relasi tersebut kosong. Properti `merchant_name` menggunakan nama toko apabila tersedia, kemudian beralih ke nama lengkap akun atau username sebagai fallback. Pendekatan ini menjaga katalog tetap informatif meskipun data profil toko belum lengkap.

    11. **Validasi Parameter Filter Katalog:** Parameter pencarian berasal dari query string sehingga dapat berisi nilai kosong, kategori yang tidak dikenal, harga dengan format tidak valid, atau pilihan pengurutan yang tidak tersedia. Saya memastikan nilai-nilai tersebut dinormalisasi sebelum digunakan dalam proses filter. Harga yang tidak dapat dikonversi ditangani sebagai filter yang tidak berlaku, sedangkan kategori dan pilihan pengurutan yang tidak dikenal dikembalikan ke perilaku default agar tidak menimbulkan kesalahan yang tidak perlu.

    12. **Integritas Data Wishlist:** Implementasi wishlist yang hanya mengandalkan pemeriksaan frontend berpotensi menghasilkan entri duplikat ketika pengguna menekan tombol favorit berkali-kali atau mengirim request secara bersamaan. Saya menggunakan `UniqueConstraint` pada kombinasi `customer` dan `bag` untuk menjaga agar satu customer tidak menyimpan paket yang sama lebih dari sekali. Saya juga membedakan hak akses customer, merchant, dan guest agar fitur favorit tidak dapat digunakan oleh peran yang tidak sesuai.

    13. **Metode HTTP dan Validasi Endpoint AJAX:** Endpoint yang mengubah data seharusnya tidak dapat dipanggil sembarangan melalui request baca biasa. Saya meninjau penggunaan pembatasan metode HTTP seperti `require_POST` untuk operasi perubahan data, serta penanganan payload JSON yang tidak valid. Untuk fitur wishlist, pembaruan stok, dan perubahan status paket, saya mempertimbangkan respons kesalahan yang sesuai agar frontend dapat membedakan permintaan yang gagal dari permintaan yang berhasil.

    14. **Validasi Unggahan Foto:** Pemeriksaan ekstensi file saja tidak cukup untuk memastikan bahwa berkas yang diunggah benar-benar layak digunakan sebagai gambar. Saya menerapkan batas ukuran unggahan sebesar 5 MB dan pemeriksaan tipe konten gambar pada form. Saya juga mempertahankan kemungkinan penggunaan gambar melalui URL sebagai alternatif ketika foto lokal tidak tersedia. Validasi tipe konten tetap merupakan pemeriksaan awal, bukan jaminan penuh bahwa berkas aman; validasi berkas yang lebih kuat masih diperlukan untuk penggunaan produksi.

    15. **Konsistensi Antara Respons API dan Tampilan Frontend:** Data yang dikembalikan backend harus memiliki format yang konsisten dengan kebutuhan komponen katalog dan halaman detail. Saya menggunakan metode `to_dict()` pada model `SurpriseBag` untuk menyajikan data seperti harga, persentase diskon, kategori, stok, informasi merchant, dan URL detail. Saya meninjau konsistensi format tersebut agar komponen frontend tidak perlu menghitung ulang informasi bisnis yang seharusnya ditentukan oleh backend.

    16. **Penanganan Wishlist untuk Paket Nonaktif:** Menghapus paket dari wishlist dan menambahkan paket ke wishlist merupakan dua tindakan dengan konsekuensi berbeda. Customer seharusnya masih dapat menghapus paket nonaktif dari daftar favoritnya, tetapi tidak boleh menambahkannya kembali sebagai pilihan aktif. Saya mempertimbangkan perbedaan kondisi tersebut dalam logika endpoint wishlist agar daftar favorit tidak mempertahankan alur yang membingungkan setelah sebuah penawaran dinonaktifkan merchant.

    17. **Kualitas Pengujian dan Skenario Edge Case:** AI cenderung lebih mudah menghasilkan pengujian untuk skenario normal daripada kombinasi kondisi yang tidak biasa. Saya memperluas evaluasi dengan menguji batas diskon, jam pengambilan yang tidak valid, stok negatif, pengguna tanpa profil merchant, akses lintas pemilik, paket nonaktif, koordinat tidak valid, serta perilaku wishlist pada berbagai status pengguna. Pendekatan ini membantu mengidentifikasi masalah yang tidak selalu terlihat ketika aplikasi hanya diuji melalui alur penggunaan normal.

    18. **Evaluasi Integrasi Antarmodul:** Modul Surprise Bag tidak berdiri sendiri karena berhubungan dengan autentikasi, profil pengguna, Merchant Store, dan Order. Saya meninjau asumsi yang dibuat oleh AI mengenai nama field, relasi model, URL, serta peran pengguna agar implementasi tidak hanya benar secara lokal, tetapi juga sesuai dengan struktur proyek LastBite secara keseluruhan. Integrasi tetap perlu diverifikasi melalui pengujian aplikasi karena keberhasilan satu fungsi secara terpisah tidak menjamin keseluruhan alur transaksi berjalan benar.

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
