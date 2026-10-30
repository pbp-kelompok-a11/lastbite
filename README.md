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

    ## AI Disclosure
    Dalam pengerjaan Proyek LastBite pada Merchant Store : Direktori Toko & Integrasi Public API
    saya Fathir atha rizki tasril menggunakan AI sebagai menyusun antarmuka peta dan pencarian asinkron, memperbaiki pencarian koordinat dari alamat,menambahkan fitur foto toko,menyelaraskan hak akses dan pengujian dan penulisan rangkaian unit test.

     **Tools yang Digunakan:** Claude

     **Bagian yang Dibantu AI:**
     1. Menyusun antarmuka peta interaktif dengan Leaflet dan tile OpenStreetMap: pin toko, pencarian nama atau alamat secara asinkron dengan `fetch`,
     2. pencarian lokasi lewat endpoint geocode, serta tombol lokasi per toko.
     3. Menampilkan lokasi toko pada halaman detail: peta OpenStreetMap dengan pin dan label nama toko, serta pencarian koordinat dari alamat melalui Nominatim
     4. Merapikan indentasi penulisan dan format berkas CSS modul (`merchant_directory.css`, `merchant_store.css`, `merchant_wishlist.css`).
     5. Memberikan langkah" dalam menyusun halaman Wishlist dengan tab Merchant dan Surprise Bags, kartu toko.


    #### Analisis Kritis Keterbatasan AI & Penyesuaian Implementasi
    1. **Akurasi Geocoding dan Batas Nominatim:** Alamat panjang atau hasil salin dari peta sering gagal dicari. Kueri cadangan (nama tempat + kecamatan + kabupaten/kota, lalu kecamatan + kabupaten/kota) bersifat heuristik berdasarkan pola penulisan alamat Indonesia, sehingga pin dapat berada di pusat area, bukan di titik persis toko.
    2. **Ketergantungan pada Layanan Publik:** Peta bergantung pada tile OpenStreetMap dan Nominatim yang dapat lambat, membatasi akses, atau tidak tersedia.Antarmuka menampilkan peta umum dan pesan status saat pencarian lokasi gagal, tetapi ketersediaan layanan dari server PWS belum dibuktikan oleh pengujian otomatis. Penggunaan tile publik juga tidak ditujukan untuk lalu lintas besar.
    3. **Perubahan Cakupan Hak Akses:** Requirement menyebut Guest dan Customer dapat membaca direktori dan detail toko. Atas keputusan kelompok, halaman detail kini mewajibkan login; daftar toko dan API pencarian tetap terbuka untuk Guest. Perubahan ini membuat beberapa pengujian lama gagal, lalu pengujian disesuaikan menjadi tamu diarahkan ke login dan pengguna yang login dapat membuka detail. Perubahan ini disengaja dan perlu dipertimbangkan terhadap bunyi requirement.
    4. **Keterbatasan Membaca Desain Figma:** ukuran font, jarak, dan warna diperkirakan dari gambar berskala dan perlu disetel berulang. sehingga perlu di stel manual
    5. **Perubahan Lintas Modul:** Penyesuaian navbar dan halaman profil menyentuh modul akun milik anggota lain. Perubahan tersebut dibatasi seminimal mungkin dan digabung melalui Git dengan branch `dev`. Merge yang saya lakukan berjalan tanpa konflik, tetapi hal itu tidak membuktikan semua fitur anggota lain tetap berfungsi tanpa diuji ulang.
    6. **Instruksi AI Tidak Selalu Sesuai Kondisi Berkas Sebenarnya:**
    banyak sekali yang saya temukan bahwa langkah atau saran dari AI harus dipahami dan perlu disesuaikan.
    7. **Deployment PWS dan Konfigurasi:** AI tidak memiliki akses ke PWS. Variabel environment dan migrasi database tetap harus saya atur dan jalankan sendiri di server, dan keberhasilannya diverifikasi lewat situs yang berjalan.

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

    # AI Disclosure & Analisis Kritis Keterbatasan AI

    **Modul Community: Food Hack & Review**

    Dalam pengembangan Proyek LastBite pada Modul Community, saya memanfaatkan AI sebagai asisten teknis untuk membantu memecahkan permasalahan logika pemrograman, mengeksplorasi pendekatan implementasi, serta memahami penggunaan Django dalam pengembangan aplikasi web. Bantuan AI juga digunakan dalam penyusunan dan penyesuaian kode, pengembangan interaksi AJAX, debugging, integrasi antarmodul, dan pengujian fungsional. Kebutuhan, cakupan fitur, serta alur penggunaan Community ditentukan berdasarkan rancangan yang saya susun, sedangkan hasil implementasinya ditinjau agar sesuai dengan kebutuhan proyek.

    **Tools yang Digunakan:** ChatGPT dan OpenAI Codex.

    ### Bagian yang Dibantu AI

    1. **Perancangan Struktur Model Community:** Membantu mengevaluasi struktur model `CommunityPost` yang digunakan untuk mengelola Food Hack dan Review, termasuk relasi terhadap pengguna, komentar, Like, dan pesanan.

    2. **Pengembangan CRUD Food Hack:** Membantu memecahkan logika pembuatan, pengeditan, dan penghapusan Food Hack melalui Django views dan forms, termasuk pengaturan hak akses berdasarkan kepemilikan postingan.

    3. **Validasi Form dan Model:** Memberikan referensi penerapan validasi melalui `ModelForm` dan metode `clean()` agar input postingan, komentar, dan Review memenuhi ketentuan masing-masing fitur.

    4. **Implementasi Community Feed:** Membantu menyusun pendekatan untuk menggabungkan Food Hack dan Review dalam satu halaman, termasuk pengelolaan tab kategori dan penyajian informasi setiap postingan.

    5. **Pencarian, Filtering, dan Sorting:** Membantu mengembangkan logika pencarian berdasarkan konten postingan, pengurutan berdasarkan waktu, jumlah Like, atau rating, serta penanganan parameter filter yang tidak sesuai.

    6. **Pengembangan Pagination:** Memberikan referensi penggunaan Django `Paginator` untuk membatasi jumlah postingan yang ditampilkan dan mempertahankan parameter pencarian ketika pengguna berpindah halaman.

    7. **Implementasi Like Berbasis AJAX:** Membantu memecahkan logika penambahan dan pembatalan Like pada Food Hack, termasuk penyimpanan status pengguna serta pembaruan jumlah Like tanpa memuat ulang halaman.

    8. **Pengembangan Komentar dan Nested Replies:** Membantu menyusun mekanisme pembuatan, pengeditan, penghapusan, dan pembalasan komentar, termasuk pengelolaan relasi komentar induk dan balasan melalui AJAX.

    9. **Integrasi Review dengan Order:** Membantu merumuskan mekanisme Review berdasarkan pesanan berstatus Completed, termasuk pemeriksaan kepemilikan Order, validasi rating, dan pembatasan satu Review per transaksi.

    10. **Pengembangan Balasan Resmi Merchant:** Membantu mengevaluasi mekanisme pemberian balasan terhadap Review oleh Merchant yang memiliki toko terkait, termasuk pengelolaan balasan yang sudah dibuat.

    11. **Pengembangan Antarmuka Community:** Memberikan referensi penyusunan Django templates, komponen HTML yang digunakan berulang, CSS, dan JavaScript agar tampilan Food Hack, Review, serta interaksi pengguna tetap konsisten.

    12. **Debugging dan Pengujian:** Membantu mengidentifikasi kesalahan implementasi, mengevaluasi penggunaan Django ORM, serta menyusun dan menyesuaikan unit test untuk validasi, CRUD, hak akses, dan integrasi antarmodul.

    ### Analisis Kritis Keterbatasan AI & Penyesuaian Implementasi

    1. **Perbedaan Aturan Bisnis Food Hack dan Review:** Meskipun Food Hack dan Review ditampilkan dalam satu Community Feed, keduanya memiliki kebutuhan data yang berbeda. Food Hack digunakan untuk membagikan tips pemanfaatan makanan, sedangkan Review merupakan penilaian terhadap transaksi yang telah diselesaikan. Saya meninjau penggunaan `post_type` pada model `CommunityPost` beserta validasinya agar Food Hack tidak memerlukan rating atau relasi Order, sementara Review harus memenuhi persyaratan tersebut. Pendekatan ini memungkinkan penggunaan struktur postingan bersama tanpa mengabaikan aturan bisnis masing-masing fitur.

    2. **Konsistensi Validasi antara Model dan Form:** Validasi yang hanya ditempatkan pada antarmuka atau form berpotensi dilewati ketika data dibuat melalui jalur lain. Saya mengevaluasi pembagian tanggung jawab antara validasi `ModelForm` dan metode `clean()` pada model untuk menjaga konsistensi data Community. Perlu diperhatikan bahwa `save()` pada Django tidak otomatis menjalankan `full_clean()`, sehingga jalur penyimpanan yang tidak melalui form tervalidasi memerlukan pemeriksaan tersendiri. Hal ini menjadi perhatian agar aturan data tidak hanya berlaku pada alur penggunaan normal.

    3. **Keamanan Hak Akses pada CRUD Food Hack:** Pengguna yang telah login tidak seharusnya memperoleh izin untuk mengubah seluruh postingan. Saya meninjau pembatasan objek berdasarkan `author=request.user` pada operasi edit dan hapus agar pengguna hanya dapat mengelola Food Hack miliknya sendiri. Pemeriksaan dilakukan pada backend, bukan hanya melalui penyembunyian tombol di antarmuka. Dengan demikian, perubahan ID postingan pada URL tidak dapat digunakan sebagai jalan pintas untuk mengakses operasi milik pengguna lain.

    4. **Validasi Kepemilikan Komentar:** Sistem komentar memerlukan pembatasan hak akses yang terpisah dari postingan induknya. Penulis Food Hack tidak otomatis memiliki kewenangan untuk mengedit seluruh komentar yang diberikan pengguna lain. Oleh karena itu, operasi pengeditan dan penghapusan komentar perlu memeriksa identitas penulis komentar yang bersangkutan. Pemisahan ini menjaga agar hak pengelolaan postingan tidak disamakan dengan hak pengelolaan komentar.

    5. **Integritas Relasi Nested Replies:** Implementasi komentar bertingkat tidak cukup hanya menyimpan ID komentar induk yang dikirim dari frontend. Tanpa validasi tambahan, balasan berpotensi dikaitkan dengan komentar dari postingan berbeda atau membentuk relasi yang tidak sesuai. Saya mengevaluasi penggunaan relasi `parent` pada `CommunityComment` beserta pemeriksaan kesesuaian postingan induk. Pendekatan ini menjaga struktur diskusi tetap konsisten dan mencegah terbentuknya hubungan komentar yang tidak valid.

    6. **Konsistensi Like antara Frontend dan Database:** Pembaruan jumlah Like secara langsung melalui JavaScript dapat menimbulkan perbedaan dengan kondisi database apabila request gagal atau status pengguna tidak sesuai. Implementasi menggunakan endpoint POST untuk memproses perubahan Like, kemudian mengembalikan status `has_upvoted` dan `upvote_count` kepada frontend. Saya meninjau agar tampilan mengikuti respons backend, bukan menentukan jumlah Like secara mandiri. Dengan demikian, database tetap menjadi sumber utama informasi interaksi pengguna.

    7. **Risiko Permintaan Like Berulang:** Interaksi AJAX memungkinkan pengguna mengirimkan beberapa request dalam waktu berdekatan, misalnya ketika tombol Like ditekan berulang kali. Jika perubahan hanya dilakukan dengan menambah atau mengurangi angka tanpa memeriksa relasi pengguna, jumlah Like berpotensi tidak konsisten. Implementasi menggunakan mekanisme toggle berdasarkan status Like yang tersimpan dan transaksi database pada proses perubahan. Namun, pengujian pada skenario request bersamaan tetap diperlukan untuk memastikan perilakunya sesuai pada lingkungan deployment.

    8. **Penyesuaian Filter dan Sorting Berdasarkan Jenis Konten:** Food Hack dan Review mempunyai parameter pengurutan yang berbeda. Pengurutan berdasarkan jumlah Like relevan untuk Food Hack, sedangkan pengurutan berdasarkan rating lebih sesuai untuk Review. Saya mengevaluasi pemisahan pilihan filter berdasarkan kategori agar parameter yang tidak relevan tidak menghasilkan perilaku yang membingungkan. Nilai parameter yang tidak dikenal juga perlu ditangani dengan pilihan default sehingga Community Feed tetap dapat digunakan.

    9. **Efisiensi Query pada Community Feed:** Community Feed menampilkan informasi yang berasal dari beberapa relasi database, seperti penulis, Order, jumlah Like, dan komentar. Jika seluruh data diambil menggunakan query terpisah pada setiap postingan, jumlah query dapat meningkat seiring bertambahnya konten. Implementasi memanfaatkan `select_related()`, anotasi `Count()`, dan `Exists()` untuk memperoleh informasi yang diperlukan. Saya juga meninjau penggunaan pagination sepuluh postingan per halaman agar sistem tidak memuat seluruh konten sekaligus. Efektivitas optimasi tetap perlu dinilai melalui pengujian query pada jumlah data yang lebih besar.

    10. **Konsistensi Pencarian dan Pagination Berbasis AJAX:** Pencarian asinkron memerlukan koordinasi antara parameter pencarian, kategori aktif, pengurutan, dan halaman yang sedang ditampilkan. Jika parameter tersebut tidak dipertahankan secara konsisten, pengguna dapat memperoleh hasil yang berbeda ketika berpindah halaman atau mengganti filter. Implementasi memisahkan respons halaman penuh dan respons parsial untuk Community Feed. Saya meninjau pendekatan ini agar perubahan hasil pencarian tidak memerlukan pemuatan ulang seluruh halaman, tetapi tetap mengikuti kondisi filter yang dipilih pengguna.

    11. **Validasi Review Berdasarkan Transaksi Completed:** Review tidak boleh dibuat hanya berdasarkan pilihan produk atau Merchant yang dikirimkan dari browser karena informasi tersebut dapat dimanipulasi. Saya mengevaluasi mekanisme `ReviewForm` agar pilihan Order dibatasi pada transaksi berstatus `COMPLETED` milik Customer yang sedang login. Kepemilikan dan status Order diperiksa kembali pada backend sebelum Review disimpan. Pendekatan ini menjaga agar Review yang terhubung dengan transaksi benar-benar berasal dari Customer yang memenuhi persyaratan.

    12. **Pencegahan Duplikasi Review dan Race Condition:** Pemeriksaan apakah sebuah Order sudah memiliki Review berpotensi tidak cukup ketika dua request dikirim hampir bersamaan. Implementasi menggunakan `transaction.atomic()` dan `select_for_update()` pada proses pembuatan Review, serta pembatasan keunikan relasi Order pada database. Saya meninjau pendekatan tersebut agar satu transaksi tidak menghasilkan beberapa Review. Namun, keberhasilan pengujian lokal tidak otomatis menjamin perilaku konkurensi yang identik pada seluruh jenis database, sehingga pengujian lanjutan tetap menjadi pertimbangan.

    13. **Pembatasan Balasan Resmi Merchant:** Status sebagai Merchant tidak otomatis memberikan hak untuk membalas seluruh Review. Merchant harus memiliki hubungan dengan toko yang menerima pesanan terkait Review tersebut. Saya mengevaluasi validasi kepemilikan melalui relasi Review, Order, dan Merchant Store agar balasan hanya dapat diberikan oleh pihak yang berwenang. Penggunaan `OneToOneField` pada model balasan juga menjaga agar setiap Review hanya mempunyai satu tanggapan resmi Merchant, yang dapat diperbarui apabila diperlukan.

    14. **Keamanan HTTP Method dan Request AJAX:** Operasi yang mengubah data tidak seharusnya menggunakan request GET karena metode tersebut ditujukan untuk pengambilan informasi. Saya meninjau penggunaan request POST dan pembatasan metode seperti `@require_POST` pada interaksi yang melakukan perubahan data. Perlindungan CSRF Django juga perlu dipertahankan pada request AJAX yang relevan. Langkah ini memastikan keamanan operasi tidak hanya bergantung pada tombol atau validasi yang tersedia di frontend.

    15. **Penggunaan Komponen Template dan Pemeliharaan Antarmuka:** Pengembangan antarmuka dengan bantuan AI berpotensi menghasilkan struktur HTML yang berulang apabila setiap halaman dibuat secara terpisah. Saya mengevaluasi penggunaan template parsial untuk elemen yang dipakai pada beberapa bagian Community, seperti komponen reaksi Food Hack, rating Review, dan pilihan sorting. Pendekatan tersebut membantu menjaga konsistensi antartampilan dan mempermudah perubahan desain. Meskipun demikian, pemisahan komponen perlu tetap mempertimbangkan keterbacaan agar struktur template tidak menjadi terlalu kompleks.

    16. **Evaluasi Integrasi Antarmodul dan Pengujian:** Modul Community bergantung pada autentikasi dari Accounts, data transaksi dari Order, serta informasi Merchant dari modul terkait. Solusi yang dihasilkan AI perlu disesuaikan dengan nama field, relasi model, URL, dan aturan akses yang digunakan dalam repository kelompok. Saya meninjau kesesuaian implementasi tersebut melalui pemeriksaan kode, debugging, dan pengujian fungsional. Pengujian juga perlu mencakup skenario khusus, seperti pengguna tanpa izin, input tidak valid, Order yang belum Completed, dan upaya membuat Review ganda. Proses evaluasi serta perbaikan kode tersebut dapat melibatkan bantuan AI, sehingga tidak seluruh penyesuaian diklaim sebagai hasil penulisan manual.

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
