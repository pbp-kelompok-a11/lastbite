# LastBite

## Deskripsi Aplikasi

LastBite adalah platform marketplace yang menghubungkan merchant makanan (bakery, kafe, restoran) dengan pembeli di sekitar kampus dan area kos, khusus untuk stok makanan yang mendekati jam tutup toko. Setiap hari, banyak merchant terpaksa membuang roti, nasi, dan pastry yang sebenarnya masih layak konsumsi karena tidak habis terjual. Di sisi lain, mahasiswa dan pekerja muda dengan budget terbatas sering kesulitan mendapat makanan berkualitas dengan harga terjangkau. LastBite mempertemukan kedua kebutuhan ini. Merchant memposting "surprise bag" berisi stok tersisa dengan harga diskon 30-50%, pembeli bisa menemukan deal aktif di sekitar mereka lewat peta interaktif, memesan lewat aplikasi, dan mengambilnya langsung ke toko menggunakan kode QR sebelum jam tutup. Selain menghemat pengeluaran pembeli dan menyelamatkan pemasukan merchant, setiap transaksi di LastBite turut mengurangi food waste, dampak yang dapat dilihat penggunanya lewat estimasi kilogram makanan terselamatkan dan jejak karbon yang berhasil dihindari.

### Sub-tema
Sustainable Food & Diet, dengan elemen Waste Management di dalamnya (food waste reduction).

### Bentuk Aplikasi

Marketplace lokal yang menghubungkan merchant (bakery/kafe/resto) yang memiliki stok makanan mendekati kedaluwarsa atau menjelang tutup toko, dengan pembeli di sekitar kampus/kos yang ingin membeli dengan harga diskon 30-50%.

### Target Pengguna & Masalah yang Diselesaikan

Target pengguna:

Pembeli: mahasiswa & pekerja muda dengan budget terbatas, yang ingin makan enak/hemat dan responsif terhadap deal instan.
Merchant: bakery, kafe, warung, resto yang rutin memiliki stok makanan tersisa tiap tutup toko dan selama ini hanya dibuang.

Masalah: 

Setiap hari, merchant makanan (terutama bakery/kafe) membuang stok layak konsumsi karena tidak habis terjual sebelum tutup. Di sisi lain, banyak mahasiswa/pekerja muda yang budget-nya ketat dan ingin membeli makanan berkualitas dengan harga lebih murah. LastBite menjembatani dua kebutuhan ini secara real-time: merchant mendapat pemasukan tambahan dari stok yang harusnya rugi total, pembeli mendapat makanan enak dengan harga diskon, dan food waste berkurang sebagai dampak sampingnya.

## Daftar Modul Rencana dan Pembagian Modul

### 1. Modul Surprise Bag: Surplus Food Inventory
* **Penanggung Jawab:** [Nama Anggota 1]
* **Data Utama:** `SurpriseBag`

Modul ini mengelola makanan surplus yang ditawarkan oleh Merchant kepada Customer dalam bentuk Surprise Bag.

#### CRUD
| Aksi | Deskripsi |
| :--- | :--- |
| **Create** | Merchant membuat Surprise Bag baru (nama, deskripsi, kategori, harga normal, harga diskon, stok, dan waktu pengambilan). |
| **Read** | Guest dan Customer dapat melihat katalog Surprise Bag yang tersedia. |
| **Update** | Merchant dapat mengubah informasi Surprise Bag (harga diskon, stok, dan waktu pengambilan). |
| **Delete** | Merchant dapat menghapus atau menonaktifkan Surprise Bag yang sudah tidak tersedia. |

#### AJAX / HTMX & Filter
* Filter katalog berdasarkan kategori, rentang harga, dan ketersediaan stok tanpa reload halaman penuh.
* Perubahan jumlah stok dapat diperbarui secara asinkron.

#### Autentikasi
* **Guest:** hanya dapat melihat katalog.
* **Customer:** dapat melihat katalog dan memesan Surprise Bag melalui Modul Order.
* **Merchant:** hanya dapat membuat, mengubah, dan menghapus Surprise Bag milik tokonya sendiri.

#### Public API
* **Open Food Facts API** digunakan sebagai sumber informasi pendukung produk makanan (nama produk, kategori, atau gambar).
* Data yang bersifat khusus untuk LastBite (merchant, harga diskon, stok, dan waktu pickup) tetap dikelola di database aplikasi.

---

### 2. Modul Order: Pemesanan & Status Pickup
* **Penanggung Jawab:** [Nama Anggota 2]
* **Data Utama:** `Order`

Modul ini mengelola transaksi antara Customer dan Merchant, mulai dari pemesanan hingga makanan selesai diambil.

#### CRUD
| Aksi | Deskripsi |
| :--- | :--- |
| **Create** | Customer membuat pesanan untuk Surprise Bag yang tersedia. |
| **Read** | Customer melihat detail dan riwayat pesanannya; Merchant melihat pesanan yang masuk ke tokonya. |
| **Update** | Merchant memperbarui status pesanan (misalnya: Pending → Ready to Pickup → Completed). |
| **Delete** | Customer dapat membatalkan pesanan yang masih memenuhi syarat pembatalan. |

#### AJAX / HTMX & Interaktivitas
* Perubahan status pesanan dilakukan secara asinkron.
* Konfirmasi pengambilan makanan dapat dilakukan melalui modal atau komponen interaktif tanpa reload penuh.
* Informasi stok atau status pesanan dapat diperbarui secara dinamis.

#### Autentikasi
* **Customer:** hanya dapat melihat dan mengelola pesanan miliknya sendiri.
* **Merchant:** hanya dapat melihat dan mengubah pesanan yang berkaitan dengan tokonya.
* **Guest:** tidak dapat membuat atau melihat data transaksi.

#### Relasi dengan Modul Lain
* `Order` mengambil data `SurpriseBag` dari Modul 1.
* Status Completed menjadi dasar pencatatan otomatis `ImpactLog` pada Modul 5.
* `Order` berstatus Completed menjadi syarat Customer untuk memberikan review kepada merchant pada Modul 4.
* Modul ini tidak membutuhkan Public API tambahan karena fokus utamanya adalah pengelolaan transaksi internal LastBite.

---

### 3. Modul Merchant Store: Direktori Toko & Pencarian Lokasi
* **Penanggung Jawab:** [Nama Anggota 3]
* **Data Utama:** `MerchantStore`

Modul ini mengelola profil toko milik Merchant sekaligus menyediakan direktori merchant yang dapat dijelajahi oleh Guest dan Customer.

#### CRUD
| Aksi | Deskripsi |
| :--- | :--- |
| **Create** | Merchant membuat profil toko yang berisi nama toko, alamat, kontak bisnis, dan jam operasional. |
| **Read** | Guest dan Customer melihat daftar serta detail merchant, termasuk lokasi dan rata-rata rating. |
| **Update** | Merchant memperbarui alamat, kontak, jam operasional, dan informasi profil lainnya. |
| **Delete** | Merchant dapat menghapus atau menonaktifkan profil tokonya. |

#### AJAX / HTMX & Filter
* Pencarian merchant dilakukan secara asinkron.
* Filter berdasarkan kategori merchant dan radius jarak (1 km, 3 km, 5 km).
* Hasil pencarian dapat diperbarui tanpa reload halaman penuh.

#### Autentikasi
* **Guest & Customer:** hanya dapat membaca informasi merchant.
* **Merchant:** hanya dapat membuat, mengubah, dan menghapus profil tokonya sendiri.

#### Public API
* **OpenStreetMap Nominatim API** digunakan untuk melakukan geocoding alamat toko menjadi koordinat latitude dan longitude, mendukung pencarian merchant berdasarkan radius jarak.

#### Fitur Pendukung
* Customer dapat menambahkan atau menghapus merchant dari wishlist/favorite (fitur relasi pendukung, bukan entitas data utama).

---

### 4. Modul Community: Review & Food Hack
* **Penanggung Jawab:** [Nama Anggota 4]
* **Data Utama:** `CommunityPost`

Modul ini menangani seluruh konten yang dibuat Customer dalam domain komunitas (review merchant dan tips food hack) yang disimpan dalam satu entitas `CommunityPost` melalui pembeda field `post_type`.

#### Struktur Model `CommunityPost`
* `author` → FK ke User
* `post_type` → `review` atau `food_hack`
* `related_order` → FK ke Order (wajib untuk review, null untuk food hack)
* `rating` → Integer 1–5 (digunakan untuk review)
* `title`, `content`, `created_at`, `updated_at`

#### CRUD
| Aksi | Deskripsi |
| :--- | :--- |
| **Create** | Customer membuat review (syarat: punya Order Completed) atau membuat food hack (tanpa syarat transaksi). |
| **Read** | Guest dan Customer membaca review pada halaman merchant serta food hack pada halaman komunitas. |
| **Update** | Customer dapat mengubah post miliknya sendiri. |
| **Delete** | Customer dapat menghapus post miliknya sendiri. |

#### AJAX / HTMX & Interaktivitas
* Form review dan food hack dapat dikirim secara asinkron.
* Fitur upvote/like pada food hack berjalan tanpa reload halaman penuh.

#### Autentikasi
* **Guest:** hanya dapat membaca konten komunitas.
* **Customer:** dapat membuat review dan food hack setelah login, serta hanya bisa mengubah dan menghapus konten miliknya sendiri.

#### Public API
* **TheMealDB API** digunakan pada halaman food hack untuk menampilkan rekomendasi resep terkait berdasarkan bahan atau topik makanan yang dibahas dalam posting.

#### Relasi dengan Modul Lain
* Rating dari `CommunityPost` bertipe review diagregasi menjadi rata-rata rating merchant dan ditampilkan pada Modul 3.

---

### 5. Modul Eco Impact: Impact Journal
* **Penanggung Jawab:** [Nama Anggota 5]
* **Data Utama:** `ImpactLog`

Mencatat dan menampilkan dampak ekonomi serta lingkungan yang dihasilkan Customer melalui aktivitas penyelamatan makanan.

#### CRUD
| Aksi | Deskripsi |
| :--- | :--- |
| **Create** | Sistem membuat `ImpactLog` secara otomatis ketika Order berstatus Completed; Customer juga dapat membuat catatan dampak secara manual. |
| **Read** | Customer melihat riwayat penghematan dan dampak lingkungan melalui halaman jurnal dan dashboard. |
| **Update** | Customer dapat mengubah catatan dampak yang dibuat secara manual. |
| **Delete** | Customer dapat menghapus catatan manual miliknya sendiri. |

#### Perhitungan Dampak
* Menghitung total uang yang dihemat Customer.
* Mengestimasi jumlah emisi karbon yang berhasil dicegah berdasarkan makanan yang diselamatkan.
* Menampilkan akumulasi dampak dalam bentuk ringkasan dan grafik.

#### AJAX / HTMX & Filter
* Dashboard diperbarui secara asinkron.
* Data dapat difilter berdasarkan periode (mingguan atau bulanan) tanpa reload halaman penuh.

#### Autentikasi
* Data jurnal dan statistik hanya dapat diakses secara privat oleh Customer yang bersangkutan.

#### Public API
* **Climatiq API** digunakan sebagai sumber faktor emisi untuk mendukung estimasi dampak karbon dari makanan yang berhasil diselamatkan.

#### Relasi dengan Modul Lain
* `ImpactLog` menggunakan data transaksi dari Modul 2 berdasarkan Order yang telah berstatus Completed.

---

## Ringkasan Pembagian Modul

| No. | Modul | Data Utama | Public API | Fokus Utama |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Surprise Bag | `SurpriseBag` | Open Food Facts | CRUD surplus food + filter katalog |
| **2** | Order | `Order` | - | CRUD transaksi + status pickup |
| **3** | Merchant Store | `MerchantStore` | OpenStreetMap Nominatim | CRUD toko + pencarian radius lokasi |
| **4** | Community | `CommunityPost` | TheMealDB | CRUD review/food hack + interaksi komunitas |
| **5** | Eco Impact | `ImpactLog` | Climatiq | CRUD jurnal + agregasi dampak |

## User Roles

Aplikasi LastBite memiliki tiga jenis peran pengguna dengan hak akses yang berbeda di setiap modul.

### 1. Guest
Pengguna yang belum login. Hanya dapat mengakses fitur baca (read-only).

| Modul | Akses |
| :--- | :--- |
| Surprise Bag | Melihat katalog Surprise Bag yang tersedia. |
| Order | Tidak dapat membuat atau melihat data transaksi. |
| Merchant Store | Melihat daftar dan detail merchant. |
| Community | Membaca review dan food hack. |
| Eco Impact | Tidak memiliki akses. |

### 2. Customer
Pengguna terdaftar yang berperan sebagai pembeli. Dapat memesan Surprise Bag, memberi review, dan memantau dampak dari transaksinya.

| Modul | Akses |
| :--- | :--- |
| Surprise Bag | Melihat katalog dan memesan Surprise Bag melalui Modul Order. |
| Order | Membuat, melihat riwayat, dan membatalkan pesanan miliknya sendiri. |
| Merchant Store | Melihat daftar/detail merchant serta menambah atau menghapus merchant dari wishlist. |
| Community | Membuat, mengubah, dan menghapus review (setelah Order Completed) dan food hack miliknya sendiri. |
| Eco Impact | Melihat dan mengelola jurnal dampak (`ImpactLog`) miliknya sendiri secara privat. |

### 3. Merchant
Pengguna terdaftar yang berperan sebagai penjual/pemilik toko. Mengelola stok Surprise Bag, profil toko, dan pesanan yang masuk.

| Modul | Akses |
| :--- | :--- |
| Surprise Bag | Membuat, mengubah, dan menghapus Surprise Bag milik tokonya sendiri. |
| Order | Melihat dan memperbarui status pesanan yang masuk ke tokonya. |
| Merchant Store | Membuat, mengubah, dan menghapus profil toko miliknya sendiri. |
| Community | Tidak dapat membuat review atau food hack (peran ini khusus Customer). |
| Eco Impact | Tidak memiliki akses (jurnal dampak khusus untuk Customer). |
