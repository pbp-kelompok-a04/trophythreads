# TROPHY THREADS

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
1. Modul Informasi Pertandingan (jadwal, hasil, forum diskusi):
- Tujuannya Menyajikan informasi pertandingan (tempat, jadwal, tim, dan hasil) yang akurat dan realtime untuk penggemar serta menghubungkan konten pertandingan dengan merchandise dan forum diskusi untuk penggemar.
- Fitur Utama:
  a. Create = Admin membuat jadwal pertandingan (tanggal, waktu, tempat, tim tuan/tamu, score akhir, dan jenis turnamen).
  b. Read = Match Detail (klik match): tanggal, waktu, tempat, tim tuan/tamu, score akhir, jenis turnamen, dan link ke forum diskusi.
  c. Update = Admin memperbarui status pertandingan yaitu skor akhir dan koreksi hasil.
  d. Delete = Untuk pertandingan yang dihapus karena duplikasi atau pembatalan, tampilkan alasan.
- Hak akses: Admin dan User
   
2. Modul Penjualan produk (merchandise)
- Tujuannya dimana seller akan membuat produk untuk dijual, menampilkan, dan serta memproses pembelian merchandise.
- Fitur Utama
  a. Create = Seller membuat/memposting suatu produk (merchandise).
  b. Read = menampilkan halaman detail produk (nama, harga, stok, deskripsi, rating) dari produk yang dibuat/dijual seller.
  c. Update = Seller dapat mengupdate detail (nama, harga, stok, deskripsi) dari produk yang dibuat.
  d. Delete = Seller dapat menghapus produk yang sudah dibuat dari halaman.
- Hak akses: Seller 
- Edge cases: Pembatalan & refund akan revert stok dan mengembalikan saldo ke user.
  
3. Modul Review Produk :
- Tujuannya memberi ruang bagi pembeli untuk memberi penilaian (rating) dan ulasan (review) terhadap merchandise tim.
- Fitur Utama
  a. Create = Aktif user (hanya yang pernah membeli produk) dapat membuat review: rating (1–5), deskripsi, dan tanggal pembelian (otomatis jika terhubung ke order).
  b. Read = Tampilan ringkasan serta sorting top positive / critical reviews.
  c. Update = Penulis review dapat mengedit review sendiri (batas waktu atau tanpa batas tapi tampilkan edit history).
  d. Delete = User dapat menghapus review sendiri.
- Hak akses: User dan Seller
  
4. Modul forum diskusi:
- Tujuannya sebagai forum untuk diskusi umum dengan user lainnya mengenai topik seputar pertandingan, komunitas/fandom/general, thread, dan sebagainya yang dibagi menjadi dua jenis yaitu official forum (yang dibuat Admin) dan personal forum (yang dibuat user general).
- Fitur Utama
  a. Create = membuat forum baru atau berkomentar/reply ke forum diskusi user lain yang sudah ada.
  b. Read = menampilkan halaman forum diskusi suatu topik beserta semua komentar/replies yang ada, title masing-masing forum, nama publisher, isi postingan (foto [optional] dan description).
  c. Update = mengedit postingan ataupun komentar yang telah di posting ke forum.
  d. Delete = menghapus halaman forum diskusi ataupun komentar yang telah di posting.
- Hak akses: User, Admin
  
5. Modul keranjang :
- Menyediakan tempat sementara untuk menampung item (merchandise) sebelum checkout dan untuk memfasilitasi perubahan kuantitas, memilih variasi, dan perhitungan harga. 
- Fitur Utama
  a. Create = Menambah item ke keranjang dan membuat pesanan
  b. Read = Menampilkan detail produk yang dimasukkan ke keranjang, informasi pengiriman, rincian pembayaran, dan metode pembayaran.
  c. Update = Mengubah variasi dan kuantitas dari produk yang dipilih.
  d. Delete = Menghapus produk yang ada di keranjang
- Hak akses: User

6. Modul favorit (semacam Wishlist):
- Tujuannya untuk menyimpan dan membuat halaman khusus yang menampilkan semua produk item yang disukai user.
- Fitur Utama
  a. Create = menambahkan produk item ke favorit.
  b. Read = menampilkan halaman yang isinya semua produk item di favorit.
  c. Update = mengupdate halaman dimana jika terjadi penambahan/penghapusan produk di favorit   
  d. Delete = hapus produk item dari favorit.
- Hak akses: User 
- Edge cases: Jika produk dihapus oleh seller, maka di halaman "Favorit" produk otomatis hilang atau tidak dapat ditemukan.

## Dataset
Link Dataset 

&rarr; https://shopee.co.id/officialgarudastore

Kami akan melakukan data scraping dari official store merchandise tim nasional Indonesia, yaitu Garuda. Dari informasi jumlah produk di web tersebut, terdapat 131 produk merchandise.

&rarr; https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017

Dari data set tersebut, kami melakukan filtering untuk mengambil matches dengan kata kunci "indonesia" yang menghasilkan 1169 pertandingan sepak bola yang dilakukan oleh Indonesia sebagai initial dataset aplikasi Trhopy Threads.

## Role Pengguna
*User*
- Melakukan registrasi sebagai user untuk menggunakan Trophy Threads.
- Melihat informasi pertandingan dan merchandise berbagai timnas sepak bola.
- Membeli merchandise timnas sepak bola. 
- Menyimpan merchandise sebagai favorit.
- Menambahkan komentar pada forum ataupun ulasan pada review merchandise.

*Seller Official*
- Melakukan registrasi sebagai official merchandise seller untuk menggunakan Trophy Threads.
- Menambahkan, edit, dan delete merchandise.

*Admin*
- Melakukan registrasi sebagai admin untuk menggunakan Trophy Threads.
- Menambahkan, edit, dan delete informasi pertandingan sepak bola.
- Memantau aktivitas forum.
