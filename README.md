# *TROPHY THREADS*

Link Trophy Threads &rarr; https://samuel-marcelino-trophythreads.pbp.cs.ui.ac.id/
\
Link Design Website &rarr;

## Nama Anggota Kelompok
- 2406435830 - Samuel Marcelino Tindaon
- 2406415116 - Giselle Julia Reyna
- 2406414076 - Amelia Juliawati
- 2406496214 - Febriyanti
- 2406496403 - Gusti Niera Fitri Alifa
- 2406353250 - Elsa Mayora Sidabutar

## Deskripsi Aplikasi
Trophy Threads adalah aplikasi yang dirancang untuk para penggemar sepak bola agar dapat mengikuti informasi pertandingan secara real-time. Tidak hanya menyajikan jadwal dan hasil pertandingan, aplikasi ini juga memudahkan pengguna untuk membeli merchandise dari tim sepak bola favorit mereka. Trophy Threads turut menyediakan ruang interaktif bagi komunitas penggemar sepak bola untuk berdiskusi dan berbagi pandangan seputar pertandingan. Melalui forum diskusi, pengguna dapat terhubung satu sama lain dan ikut berpartisipasi dalam percakapan seputar dunia sepak bola. Kehadiran Trophy Threads membawa pengalaman baru bagi para penggemar untuk mendukung tim favorit mereka dengan cara yang lebih interaktif dan menyenangkan.

## Daftar Modul
1. Modul Informasi Pertandingan (jadwal, hasil, forum diskusi)
2. Modul Pembelian produk (merchandise) 
- Tujuannya dimana seller menawarkan, menampilkan, dan memproses pembelian merchandise sedangkan user melakukan checkout dan pembayaran.
- Fitur Utama
  a. Create = seller membuat/memposting suatu produk (merchandise).
  b. Read = menampilkan halaman detail dan lengkap dari produk yang dibuat/dijual seller.
  c. Update = seller dapat mengupdate detail dari produk yang dibuat.
  d. Delete = seller dapat menghapus produk yang sudah dibuat dari halaman.
- Hak akses: User dan Seller
- UI/UX:
  a. Seller
  > Halaman untuk menambah produk serta detailnya (nama, harga, upload gambar, stok, dsb)
  > Halaman untuk mengedit/mengupdate detail dari produk yang sudah dibuat.
  > Halaman untuk melihat pesanan yang di checkout dan update status pesanan.
  b. User (buyer) 
  > Halaman katalog untuk mencari produk. // TODO (ini masuk sini kah?)
  > Halaman detail produk serta tombol "checkout".
  > Halaman ringkasan pesanan serta identitas dari user (buyer) serta untuk memproses dan melanjutkan ke pembayaran.
  > Halaman pembayaran di dalam aplikasi, integrasi gateway (OVO/Gopay/E-Wallet).
  > Halaman konfirmasi & status pesanan (processing, shipped, delivered).
- Edge cases: Pembatalan & refund akan revert stok dan mengembalikan saldo ke user (buyer).
4. Modul Review Produk 
5. Modul forum diskusi:
- Tujuannya sebagai forum untuk diskusi umum dengan user lainnya mengenai topik seputar pertandingan, merchandise, komunitas/fandom/general, thread, dan sebagainya.
- Fitur Utama
  a. Create = membuat forum baru atau berkomentar/reply ke forum diskusi user lain yang sudah ada.
  b. Read = menampilkan halaman forum diskusi suatu topik beserta semua komentar/replies yang ada.
  c. Update = mengedit postingan ataupun komentar yang telah di posting ke forum.
  d. Delete = menghapus halaman forum diskusi ataupun komentar yang telah di posting.
- Hak akses: User, Admin, Seller
- UI/UX:
  a. Halaman forum diskusi (kategori: general/pertandingan/merchandise/dsb).
  b. Thread list yang di sort berdasrarkan latest/recent/pinned.
  c. Thread view yang isinya postingan awal + replies threaded. Reply box berada di bawah postingan yang sebaris dengan opsi like.
- Edge cases: Long threads > collapse older replies dan offer "jump to newest".
6. Modul keranjang 
7. Modul favorit (semacam Wishlist):
- Tujuannya untuk menyimpan dan membuat halaman khusus yang menampilkan semua produk item yang disukai user.
- Fitur Utama
  a. Create = menambahkan produk item ke favorit.
  b. Read = menampilkan halaman yang isinya semua produk item di favorit.
  c. Update = // TODO 
  d. Delete = hapus produk item dari favorit.
- Hak akses: User 
- UI/UX:
  a. Tombol "added to fav" muncul di detail_product.html.
  b. Halaman "Favorit" yang menyimpan dan menampilkan daftar semua produk yang disukai user.
- Edge cases: Jika produk dihapus oleh seller maka di halaman "Favorit" produk otomatis hilang atau tidak dapat ditemukan.

## Dataset
Link Dataset 

&rarr; https://shopee.co.id/officialgarudastore

Kami akan melakukan data scraping dari official store merchandise tim nasional Indonesia, yaitu Garuda. Dari informasi jumlah produk di web tersebut, terdapat 131 produk merchandise.

&rarr; https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017

Dari data set tersebut, kami melakukan filtering untuk mengambil matches dengan kata kunci "indonesia" yang menghasilkan 1169 pertandingan sepak bola yang dilakukan oleh Indonesia sebagai initial dataset aplikasi Trhopy Threads.

## Role Pengguna
**User**
- Melakukan registrasi sebagai user untuk menggunakan Trophy Threads.
- Melihat informasi pertandingan dan merchandise berbagai timnas sepak bola.
- Membeli merchandise timnas sepak bola. 
- Menyimpan merchandise sebagai favorit.
- Menambahkan komentar pada forum ataupun ulasan pada review merchandise.

**Seller Official**
- Melakukan registrasi sebagai official merchandise seller untuk menggunakan Trophy Threads.
- Menambahkan, edit, dan delete merchandise.

**Admin**
- Melakukan registrasi sebagai admin untuk menggunakan Trophy Threads.
- Menambahkan, edit, dan delete informasi pertandingan sepak bola.
- Memantau aktivitas forum.
