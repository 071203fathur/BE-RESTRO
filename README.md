**Dokumentasi API Backend - BE-RESTRO (Aplikasi Kesehatan)**

Dokumen ini menjelaskan semua endpoint API yang tersedia untuk backend aplikasi kesehatan BE-RESTRO.

**Base URL:** <http://127.0.0.1:5001> (Port bisa berbeda tergantung konfigurasi Anda)

**Format Data Umum:**

- Request body untuk POST dan PUT umumnya menggunakan format application/json, kecuali untuk upload file yang menggunakan multipart/form-data.
- Response body selalu dalam format application/json.

**Autentikasi:**

- Sebagian besar endpoint memerlukan autentikasi menggunakan JSON Web Token (JWT).
- Kirim token JWT di header Authorization dengan format Bearer &lt;TOKEN_ANDA&gt;.

**1\. Autentikasi (/auth)**

Endpoint yang berkaitan dengan registrasi, login, dan logout pengguna.

**1.1. Registrasi Terapis**

- **Method:** POST
- **URL:** /auth/terapis/register
- **Deskripsi:** Mendaftarkan pengguna baru sebagai terapis.
- **Headers:**
  - Content-Type: application/json
- **Request Body:**
- {
- "username": "terapis_handal",
- "nama_lengkap": "Dr. Terapis Handal",
- "email": "<terapis.handal@example.com>",
- "password": "passwordkuat123"
- }
- **Response Sukses (201 Created):**
- {
- "msg": "Registrasi terapis berhasil",
- "user": {
- "id": 1,
- "username": "terapis_handal",
- "nama_lengkap": "Dr. Terapis Handal",
- "email": "<terapis.handal@example.com>",
- "role": "terapis"
- }
- }
- **Response Error:**
  - 400 Bad Request: Data tidak lengkap atau format salah.
  - 409 Conflict: Username atau email sudah terdaftar.
  - 500 Internal Server Error: Kesalahan server.

**1.2. Login Terapis**

- **Method:** POST
- **URL:** /auth/terapis/login
- **Deskripsi:** Login untuk pengguna terapis.
- **Headers:**
  - Content-Type: application/json
- **Request Body:**
- {
- "identifier": "<terapis.handal@example.com>", // Bisa email atau username
- "password": "passwordkuat123"
- }
- **Response Sukses (200 OK):**
- {
- "access_token": "&lt;TOKEN_JWT_ANDA&gt;",
- "user": {
- "id": 1,
- "username": "terapis_handal",
- "nama_lengkap": "Dr. Terapis Handal",
- "email": "<terapis.handal@example.com>",
- "role": "terapis"
- }
- }
- **Response Error:**
  - 400 Bad Request: Identifier atau password tidak diisi.
  - 401 Unauthorized: Identifier atau password salah.

**1.3. Registrasi Pasien**

- **Method:** POST
- **URL:** /auth/pasien/register
- **Deskripsi:** Mendaftarkan pengguna baru sebagai pasien.
- **Headers:**
  - Content-Type: application/json
- **Request Body:**
- {
- "username": "pasien_rajin",
- "nama_lengkap": "Budi Pasien Rajin",
- "email": "<pasien.rajin@example.com>",
- "password": "passwordpasien789",
- "nomor_telepon": "081234567890" // Opsional
- }
- **Response Sukses (201 Created):**
- {
- "msg": "Registrasi pasien berhasil",
- "user": {
- "id": 2,
- "username": "pasien_rajin",
- "nama_lengkap": "Budi Pasien Rajin",
- "email": "<pasien.rajin@example.com>",
- "role": "pasien"
- }
- }
- **Response Error:** Sama seperti registrasi terapis.

**1.4. Login Pasien**

- **Method:** POST
- **URL:** /auth/pasien/login
- **Deskripsi:** Login untuk pengguna pasien.
- **Headers:**
  - Content-Type: application/json
- **Request Body:**
- {
- "identifier": "<pasien.rajin@example.com>", // Bisa email atau username
- "password": "passwordpasien789"
- }
- **Response Sukses (200 OK):**
- {
- "access_token": "&lt;TOKEN_JWT_ANDA&gt;",
- "user": {
- "id": 2,
- "username": "pasien_rajin",
- "nama_lengkap": "Budi Pasien Rajin",
- "email": "<pasien.rajin@example.com>",
- "role": "pasien"
- }
- }
- **Response Error:** Sama seperti login terapis.

**1.5. Logout**

- **Method:** POST
- **URL:** /auth/logout
- **Deskripsi:** Logout pengguna. Sisi server tidak benar-benar "menghapus" token JWT standar, tapi endpoint ini bisa digunakan untuk logging atau jika menggunakan mekanisme blocklist token.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
- **Request Body:** Kosong.
- **Response Sukses (200 OK):**
- {
- "msg": "User '&lt;username_pengguna&gt;' logged out. Harap hapus token di sisi client."
- }
- **Response Error:**
  - 401 Unauthorized: Token tidak valid atau tidak ada.

**2\. Profil Pasien (/api/patient)**

Endpoint yang berkaitan dengan data profil pasien.

**2.1. Dapatkan Profil Pasien (Saat Ini Login)**

- **Method:** GET
- **URL:** /api/patient/profile
- **Deskripsi:** Mendapatkan detail profil lengkap dari pasien yang sedang login.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
- **Response Sukses (200 OK):**
- {
- "user_id": 2,
- "username": "pasien_rajin",
- "nama_lengkap": "Budi Pasien Rajin",
- "email": "<pasien.rajin@example.com>",
- "jenis_kelamin": "Laki-laki",
- "tanggal_lahir": "1990-05-15",
- "tempat_lahir": "Jakarta",
- "nomor_telepon": "081234567890",
- "alamat": "Jl. Sehat No. 1",
- "nama_pendamping": "Siti Pendamping",
- "diagnosis": "Post-stroke ringan",
- "catatan_tambahan": "Perlu perhatian pada gerakan motorik halus.",
- "tinggi_badan": 170,
- "berat_badan": 65.5,
- "golongan_darah": "O+",
- "riwayat_medis": "Hipertensi terkontrol",
- "riwayat_alergi": "Tidak ada",
- "updated_at": "2025-06-05T10:30:00"
- }
- **Response Error:**
  - 401 Unauthorized: Token tidak valid.
  - 403 Forbidden: Pengguna bukan pasien.
  - 404 Not Found: Profil pasien tidak ditemukan.

**2.2. Update Profil Pasien (Saat Ini Login)**

- **Method:** PUT
- **URL:** /api/patient/profile
- **Deskripsi:** Memperbarui detail profil pasien yang sedang login.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
  - Content-Type: application/json
- **Request Body (kirim hanya field yang ingin diubah):**
- {
- "nama_lengkap": "Budi Pasien Semangat",
- "nomor_telepon": "08111222333",
- "alamat": "Jl. Sehat Selalu No. 12",
- "diagnosis": "Post-stroke ringan, pemulihan baik",
- "tinggi_badan": 171
- }
- **Response Sukses (200 OK):**
- {
- "msg": "Profil pasien berhasil diperbarui",
- "profile": {
- // ... (data profil lengkap yang sudah terupdate) ...
- }
- }
- **Response Error:**
  - 400 Bad Request: Data tidak valid (misal format tanggal salah).
  - 401 Unauthorized: Token tidak valid.
  - 403 Forbidden: Pengguna bukan pasien.
  - 404 Not Found: Profil pasien tidak ditemukan.
  - 409 Conflict: Username, email, atau nomor telepon baru sudah digunakan.

**3\. Manajemen Gerakan (/api/gerakan)**

Endpoint untuk terapis mengelola perpustakaan gerakan rehabilitasi.

**3.1. Buat Gerakan Baru**

- **Method:** POST
- **URL:** /api/gerakan/
- **Deskripsi:** Terapis menambahkan gerakan baru ke perpustakaan.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
  - (Content-Type akan otomatis multipart/form-data jika mengirim file)
- **Request Body:** form-data
  - nama_gerakan (teks, wajib): "Angkat Kaki Lurus"
  - deskripsi (teks, opsional): "Berbaring, angkat satu kaki lurus ke atas."
  - foto (file, opsional): (file gambar .png, .jpg, dll.)
  - video (file, opsional): (file video .mp4, .mov, dll.)
  - model_tflite (file, opsional): (file .tflite)
- **Response** Sukses **(201 Created):**
- {
- "msg": "Gerakan berhasil dibuat",
- "gerakan": {
- "id": 1,
- "nama_gerakan": "Angkat Kaki Lurus",
- "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",
- "url_foto": "/media/gerakan/foto/uuid_namafile.jpg", // Contoh URL
- "url_video": "/media/gerakan/video/uuid_namafile.mp4",
- "url_model_tflite": "/media/gerakan/model_tflite/uuid_namafile.tflite",
- "created_by_terapis": { "id": 1, "nama_lengkap": "Dr. Terapis Handal", /\* ... \*/ },
- "created_at": "2025-06-05T11:00:00",
- "updated_at": "2025-06-05T11:00:00"
- }
- }
- **Response Error:**
  - 400 Bad Request: Data form tidak lengkap, format file salah, atau error upload.
  - 401 Unauthorized/403 Forbidden: Bukan terapis.
  - 500 Internal Server Error.

**3.2. Dapatkan Semua Gerakan**

- **Method:** GET
- **URL:** /api/gerakan/
- **Deskripsi:** Mendapatkan daftar semua gerakan (bisa diakses terapis dan pasien). Mendukung paginasi dan pencarian.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
- **Query Parameters (Opsional):**
  - page (integer, default: 1): Halaman ke-
  - per_page (integer, default: 10): Jumlah item per halaman
  - search (string): Kata kunci pencarian berdasarkan nama gerakan
- **Response Sukses (200 OK):**
- {
- "msg": "Daftar gerakan berhasil diambil",
- "gerakan": \[
- { /\* ... data gerakan 1 (serialize_full) ... \*/ },
- { /\* ... data gerakan 2 (serialize_full) ... \*/ }
- \],
- "total_items": 20,
- "total_pages": 2,
- "current_page": 1,
- "per_page": 10
- }
- **Response Error:** 401 Unauthorized.

**3.3. Dapatkan Detail Gerakan**

- **Method:** GET
- **URL:** /api/gerakan/&lt;int:gerakan_id&gt;
- **Deskripsi:** Mendapatkan detail satu gerakan berdasarkan ID.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
- **Response Sukses (200 OK):**
- {
- "msg": "Detail gerakan berhasil diambil",
- "gerakan": { /\* ... data gerakan lengkap (serialize_full) ... \*/ }
- }
- **Response Error:**
  - 401 Unauthorized.
  - 404 Not Found: Gerakan tidak ditemukan.

**3.4. Update Gerakan**

- **Method:** PUT
- **URL:** /api/gerakan/&lt;int:gerakan_id&gt;
- **Deskripsi:** Terapis memperbarui detail gerakan.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
- **Request Body:** form-data (kirim field yang ingin diubah, termasuk file jika ingin mengganti)
  - nama_gerakan (teks)
  - deskripsi (teks)
  - foto (file)
  - video (file)
  - model_tflite (file)
- **Response Sukses (200 OK):**
- {
- "msg": "Gerakan berhasil diupdate",
- "gerakan": { /\* ... data gerakan terupdate (serialize_full) ... \*/ }
- }
- **Response Error:** 400, 401, 403, 404, 500.

**3.5. Hapus Gerakan**

- **Method:** DELETE
- **URL:** /api/gerakan/&lt;int:gerakan_id&gt;
- **Deskripsi:** Terapis menghapus gerakan dari perpustakaan.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
- **Response Sukses (200 OK):**
- {
- "msg": "Gerakan berhasil dihapus"
- }
- **Response Error:** 401, 403, 404, 500.

**4\. Program Rehabilitasi (/api/program)**

Endpoint untuk terapis membuat dan meng-assign program, serta pasien melihat programnya.

**4.1. Terapis: Dapatkan Daftar Pasien**

- **Method:** GET
- **URL:** /api/program/pasien-list
- **Deskripsi:** Terapis mendapatkan daftar semua pasien untuk dipilih saat membuat program.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
- **Response Sukses (200 OK):**
- \[
- { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "<pasien.rajin@example.com>", "role": "pasien" },
- { "id": 3, "username": "siti_pasien", "nama_lengkap": "Siti Pasien", "email": "<siti.pasien@example.com>", "role": "pasien" }
- \]
- **Response Error:** 401, 403.

**4.2. Terapis: Buat & Assign Program Baru**

- **Method:** POST
- **URL:** /api/program/
- **Deskripsi:** Terapis membuat program baru dan meng-assign ke pasien.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
  - Content-Type: application/json
- **Request Body:**
- {
- "nama_program": "Rehabilitasi Lutut Minggu ke-2",
- "pasien_id": 2, // ID pasien yang dituju
- "tanggal_program": "2025-06-12", // Tanggal program ini akan dilakukan pasien
- "catatan_terapis": "Fokus pada penguatan quadrisep.",
- "status": "belum_dimulai", // Opsional, default: belum_dimulai
- "list_gerakan_direncanakan": \[
- { "gerakan_id": 1, "jumlah_repetisi_direncanakan": 12, "urutan_dalam_program": 1 },
- { "gerakan_id": 3, "jumlah_repetisi_direncanakan": 15, "urutan_dalam_program": 2 }
- \]
- }
- **Response Sukses (201 Created):**
- {
- "msg": "Program rehabilitasi berhasil dibuat dan di-assign",
- "program": { /\* ... data program lengkap (serialize_full) ... \*/ }
- }
- **Response Error:** 400, 401, 403, 404 (jika pasien atau gerakan tidak ditemukan), 500.

**4.3. Pasien: Dapatkan Program Hari Ini/Aktif**

- **Method:** GET
- **URL:** /api/program/pasien/today
- **Deskripsi:** Pasien mendapatkan program aktif yang dijadwalkan untuk hari ini atau program aktif terdekat yang belum selesai.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
- **Response Sukses (200 OK):**
- {
- "msg": "Program rehabilitasi berhasil diambil",
- "program": { /\* ... data program lengkap (serialize_full) ... \*/ }
- }
- **Response Error:**
  - 401 Unauthorized, 403 Forbidden.
  - 404 Not Found: Jika tidak ada program aktif.

**4.4. Pasien: Dapatkan Riwayat Program**

- **Method:** GET
- **URL:** /api/program/pasien/history
- **Deskripsi:** Pasien mendapatkan riwayat semua program yang pernah di-assign kepadanya (mendukung paginasi).
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
- **Query** Parameters **(Opsional):** page, per_page
- **Response Sukses (200 OK):**
- {
- "msg": "Riwayat program pasien berhasil diambil",
- "programs": \[
- { /\* ... data program 1 (serialize_full) ... \*/ },
- { /\* ... data program 2 (serialize_full) ... \*/ }
- \],
- "total_items": 5,
- "total_pages": 1,
- "current_page": 1
- }
- **Response Error:** 401, 403.

**4.5. Terapis: Dapatkan Program yang Di-assign ke Pasien Tertentu**

- **Method:** GET
- **URL:** /api/program/terapis/assigned-to-patient/&lt;int:pasien_id&gt;
- **Deskripsi:** Terapis mendapatkan riwayat program yang telah ia assign ke pasien tertentu (mendukung paginasi).
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
- **Query Parameters (Opsional):** page, per_page
- **Response Sukses (200 OK):**
- {
- "msg": "Daftar program yang di-assign ke pasien NAMA_PASIEN berhasil diambil",
- "programs": \[ /\* ... daftar program ... \*/ \],
- // ... (info paginasi) ...
- }
- **Response Error:** 401, 403, 404 (jika pasien tidak ditemukan).

**4.6. Dapatkan Detail Program Spesifik**

- **Method:** GET
- **URL:** /api/program/&lt;int:program_id&gt;
- **Deskripsi:** Mendapatkan detail program berdasarkan ID-nya. Bisa diakses oleh terapis pembuat atau pasien penerima.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
- **Response Sukses (200 OK):**
- {
- "msg": "Detail program berhasil diambil",
- "program": { /\* ... data program lengkap (serialize_full) ... \*/ }
- }
- **Response Error:** 401, 403, 404.

**4.7. Update Status Program**

- **Method:** PUT
- **URL:** /api/program/&lt;int:program_id&gt;/update-status
- **Deskripsi:** Terapis atau sistem mengubah status program (misal, dari belum_dimulai ke berjalan, atau dari berjalan ke dibatalkan). Pasien juga bisa mengubah ke berjalan.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
  - Content-Type: application/json
- **Request Body:**
- {
- "status": "berjalan" // Pilihan: "belum_dimulai", "berjalan", "selesai", "dibatalkan"
- }
- **Response Sukses (200 OK):**
- {
- "msg": "Status program berhasil diubah menjadi 'berjalan'",
- "program": { /\* ... data program ringkas (serialize_simple) dengan status terupdate ... \*/ }
- }
- **Response Error:** 400, 401, 403, 404.

**5\. Laporan Hasil Rehabilitasi (/api/laporan)**

Endpoint untuk pasien mengirimkan hasil pelaksanaan program dan untuk melihat laporan.

**5.1. Pasien: Submit Laporan Hasil Rehabilitasi**

- **Method:** POST
- **URL:** /api/laporan/submit
- **Deskripsi:** Pasien mengirimkan hasil dari program rehabilitasi yang telah dilakukan.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
  - Content-Type: application/json
- **Request Body:**
- {
- "program_rehabilitasi_id": 1, // ID program yang dilaporkan
- "tanggal_laporan": "2025-06-12", // Tanggal laporan disubmit/program dilakukan
- "total_waktu_rehabilitasi_detik": 1800, // Total waktu dalam detik
- "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",
- "detail_hasil_gerakan": \[ // Array hasil per gerakan
- {
- "gerakan_id": 1, // ID gerakan dari library
- // "program_gerakan_detail_id_asli": 1, // Opsional: ID detail dari ProgramGerakanDetail
- "urutan_gerakan_dalam_program": 1, // Urutan gerakan ini saat dilakukan
- "jumlah_sempurna": 10,
- "jumlah_tidak_sempurna": 2,
- "jumlah_tidak_terdeteksi": 0,
- "waktu_aktual_per_gerakan_detik": 300 // Waktu untuk gerakan ini (detik)
- },
- {
- "gerakan_id": 3,
- // "program_gerakan_detail_id_asli": 2,
- "urutan_gerakan_dalam_program": 2,
- "jumlah_sempurna": 15,
- "jumlah_tidak_sempurna": 0,
- "jumlah_tidak_terdeteksi": 0,
- "waktu_aktual_per_gerakan_detik": 360
- }
- \]
- }
- **Response Sukses (201 Created):**
- {
- "msg": "Laporan rehabilitasi berhasil disubmit",
- "laporan_id": 1,
- "data_laporan": { /\* ... data laporan lengkap (serialize_full dari LaporanRehabilitasi) ... \*/ }
- }
- **Response Error:** 400, 401, 403, 404 (program tidak ditemukan), 409 (laporan sudah ada), 500.

**5.2. Dapatkan Detail Laporan**

- **Method:** GET
- **URL:** /api/laporan/&lt;int:laporan_id&gt;
- **Deskripsi:** Mendapatkan detail satu laporan rehabilitasi. Bisa diakses oleh pasien pemilik atau terapis yang terkait.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt;
- **Response Sukses (200 OK):**
- {
- "msg": "Detail laporan berhasil diambil",
- "laporan": { /\* ... data laporan lengkap (serialize_full dari LaporanRehabilitasi) ... \*/ }
- }
- **Response Error:** 401, 403, 404.

**5.3. Pasien: Dapatkan Riwayat Laporan**

- **Method:** GET
- **URL:** /api/laporan/pasien/history
- **Deskripsi:** Pasien mendapatkan daftar semua laporannya (mendukung paginasi).
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PASIEN&gt;
- **Query Parameters (Opsional):** page, per_page
- **Response Sukses (200 OK):**
- {
- "msg": "Riwayat laporan pasien berhasil diambil",
- "laporan": \[ /\* ... daftar laporan ... \*/ \],
- // ... (info paginasi) ...
- }
- **Response Error:** 401, 403.

**5.4. Terapis: Dapatkan Riwayat Laporan Pasien Tertentu**

- **Method:** GET
- **URL:** /api/laporan/terapis/by-pasien/&lt;int:target_pasien_id&gt;
- **Deskripsi:** Terapis mendapatkan daftar laporan dari pasien tertentu (mendukung paginasi).
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_TERAPIS&gt;
- **Query** Parameters **(Opsional):** page, per_page
- **Response Sukses (200 OK):**
- {
- "msg": "Riwayat laporan untuk pasien NAMA_PASIEN berhasil diambil",
- "laporan": \[ /\* ... daftar laporan ... \*/ \],
- // ... (info paginasi) ...
- }
- **Response Error:** 401, 403, 404 (pasien tidak ditemukan).

**6\. Monitoring Pasien (/api/monitoring)**

Endpoint untuk terapis (atau pasien sendiri) melihat ringkasan dan tren progres rehabilitasi.

**6.1. Dapatkan Summary Monitoring Pasien**

- **Method:** GET
- **URL:** /api/monitoring/summary/pasien/&lt;int:pasien_id&gt;
- **Deskripsi:** Mendapatkan data ringkasan lengkap untuk dashboard monitoring pasien.
- **Headers:**
  - Authorization: Bearer &lt;TOKEN_PENGGUNA&gt; (Terapis atau Pasien pemilik)
- **Response Sukses (200 OK):**
- {
- "pasien_info": {
- "nama_lengkap": "Budi Pasien Rajin",
- "id_pasien_string": "PAS002",
- "user_id": 2,
- "jenis_kelamin": "Laki-laki",
- "tanggal_lahir": "15-05-1990",
- "diagnosis": "Post-stroke ringan, pemulihan baik",
- "catatan_tambahan_pasien": "Perlu perhatian pada gerakan motorik halus."
- },
- "summary_kpi": {
- "total_sesi_selesai": 5,
- "rata_rata_akurasi_persen": 85, // Dalam persen
- "rata_rata_durasi_string": "25m 30s", // Format MMm SSs atau HHh MMm SSs
- "rata_rata_durasi_detik": 1530,
- "frekuensi_latihan_per_minggu": 3.5
- },
- "trends_chart": {
- "akurasi_7_sesi_terakhir": {
- "labels": \["29 Mei", "31 Mei", "02 Jun", "04 Jun", "05 Jun"\],
- "data": \[80, 82, 85, 88, 90\] // Persentase akurasi
- },
- "durasi_7_sesi_terakhir": {
- "labels": \["29 Mei", "31 Mei", "02 Jun", "04 Jun", "05 Jun"\],
- "data": \[30, 28, 25, 26, 24\] // Durasi dalam menit
- }
- },
- "distribusi_hasil_gerakan_total": {
- "labels": \["Sempurna", "Tidak Sempurna", "Tidak Terdeteksi"\],
- "data": \[250, 30, 15\] // Jumlah total hitungan
- },
- "catatan_observasi_terbaru": \[
- {
- "tanggal": "2025-06-05",
- "catatan": "Pasien menunjukkan peningkatan signifikan minggu ini.",
- "sumber": "Terapis (Dr. Terapis Handal) - Program: Rehabilitasi Lutut Minggu ke-2"
- },
- {
- "tanggal": "2025-06-04",
- "catatan": "Latihan hari ini terasa lebih ringan.",
- "sumber": "Pasien - Laporan Program: Rehabilitasi Lutut Minggu ke-2"
- }
- \],
- "riwayat_aktivitas_monitoring": \[ // Ini adalah daftar program yang telah selesai (LaporanRehabilitasi)
- {
- "tanggal_program": "2025-06-05",
- "nama_program": "Rehabilitasi Lutut Minggu ke-2",
- "status_program": "selesai",
- "laporan_id": 1,
- "tingkat_kesulitan_dirasakan": "Sedang", // Perlu field di LaporanRehabilitasi jika mau spesifik
- "keterangan_sesi": "Semua gerakan terasa baik, sedikit pegal."
- },
- // ... item lainnya ...
- \]
- }
- **Response Error:**
  - 401 Unauthorized, 403 Forbidden.
  - 404 Not Found: Pasien tidak ditemukan atau belum ada laporan.

**7\. Penyajian File Media (/media/gerakan)**

Endpoint ini tidak memerlukan autentikasi JWT agar file bisa diakses langsung oleh tag &lt;img&gt; atau &lt;video&gt; di frontend/mobile.

**7.1. Sajikan Foto Gerakan**

- **Method:** GET
- **URL:** /media/gerakan/foto/&lt;path:filename&gt;
- **Deskripsi:** Mengakses file foto gerakan. filename adalah nama unik file yang disimpan.
- **Response:** File gambar.

**7.2. Sajikan Video Gerakan**

- **Method:** GET
- **URL:** /media/gerakan/video/&lt;path:filename&gt;
- **Deskripsi:** Mengakses file video gerakan.
- **Response:** File video.

**7.3. Sajikan Model .tflite Gerakan**

- **Method:** GET
- **URL:** /media/gerakan/model_tflite/&lt;path:filename&gt;
- **Deskripsi:** Mengakses file model .tflite gerakan.
- **Response:** File .tflite.

Dokumentasi ini akan membantu tim frontend dan mobile dalam mengintegrasikan dengan backend API Anda. Pastikan untuk selalu memperbarui dokumentasi ini jika ada perubahan pada API.