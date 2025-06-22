Dokumentasi API Backend - BE-RESTRO (Aplikasi Kesehatan)

Dokumen ini menjelaskan semua endpoint API yang tersedia untuk backend aplikasi kesehatan BE-RESTRO.

Base URL: https://be-restro-api-fnfpghddbka7d4aw.eastasia-01.azurewebsites.net

Format Data Umum:

Request body untuk POST dan PUT umumnya menggunakan format application/json, kecuali untuk upload file yang menggunakan multipart/form-data.

Response body selalu dalam format application/json.

Autentikasi:

Sebagian besar endpoint memerlukan autentikasi menggunakan JSON Web Token (JWT).

Kirim token JWT di header Authorization dengan format Bearer <TOKEN_ANDA>.

1\. API untuk Semua Pengguna (Terapis & Pasien)

Bagian ini berisi endpoint yang dapat diakses oleh pengguna dengan peran Terapis maupun Pasien, setelah mereka terautentikasi.

1.1 Autentikasi (/auth)

Endpoint yang berkaitan dengan registrasi, login, dan logout pengguna.

1.1.1 Registrasi Terapis

Method: POST

URL: /auth/terapis/register

Deskripsi: Mendaftarkan pengguna baru sebagai terapis.

Headers:

Content-Type: application/json

Request Body:

{

  "username": "terapis_handal",

  "nama_lengkap": "Dr. Terapis Handal",

  "email": "terapis.handal@example.com",

  "password": "passwordkuat123"

}

Response Sukses (201 Created):

{

  "msg": "Registrasi terapis berhasil",

  "user": {

    "id": 1,

    "username": "terapis_handal",

    "nama_lengkap": "Dr. Terapis Handal",

    "email": "terapis.handal@example.com",

    "role": "terapis"

  }

}

Response Error:

400 Bad Request: Data tidak lengkap atau format salah.

409 Conflict: Username atau email sudah terdaftar.

500 Internal Server Error: Kesalahan server.

1.1.2 Login Terapis

Method: POST

URL: /auth/terapis/login

Deskripsi: Login untuk pengguna terapis.

Headers:

Content-Type: application/json

Request Body:

{

  "identifier": "terapis.handal@example.com", // Bisa email atau username

  "password": "passwordkuat123"

}

Response Sukses (200 OK):

{

  "access_token": "<TOKEN_JWT_ANDA>",

  "user": {

    "id": 1,

    "username": "terapis_handal",

    "nama_lengkap": "Dr. Terapis Handal",

    "email": "terapis.handal@example.com",

    "role": "terapis"

  }

}

Response Error:

400 Bad Request: Identifier atau password tidak diisi.

401 Unauthorized: Identifier atau password salah.

1.1.3 Registrasi Pasien

Method: POST

URL: /auth/pasien/register

Deskripsi: Mendaftarkan pengguna baru sebagai pasien.

Headers:

Content-Type: application/json

Request Body:

{

  "username": "pasien_rajin",

  "nama_lengkap": "Budi Pasien Rajin",

  "email": "pasien.rajin@example.com",

  "password": "passwordpasien789",

  "nomor_telepon": "081234567890" // Opsional

}

Response Sukses (201 Created):

{

  "msg": "Registrasi pasien berhasil",

  "user": {

    "id": 2,

    "username": "pasien_rajin",

    "nama_lengkap": "Budi Pasien Rajin",

    "email": "pasien.rajin@example.com",

    "role": "pasien"

  }

}

Response Error: Sama seperti registrasi terapis.

1.1.4 Login Pasien

Method: POST

URL: /auth/pasien/login

Deskripsi: Login untuk pengguna pasien.

Headers:

Content-Type: application/json

Request Body:

{

  "identifier": "pasien.rajin@example.com", // Bisa email atau username

  "password": "passwordpasien789"

}

Response Sukses (200 OK):

{

  "access_token": "<TOKEN_JWT_ANDA>",

  "user": {

    "id": 2,

    "username": "pasien_rajin",

    "nama_lengkap": "Budi Pasien Rajin",

    "email": "pasien.rajin@example.com",

    "role": "pasien"

  }

}

Response Error: Sama seperti login terapis.

1.1.5 Logout

Method: POST

URL: /auth/logout

Deskripsi: Logout pengguna. Sisi server tidak benar-benar "menghapus" token JWT standar, tetapi endpoint ini bisa digunakan untuk logging atau jika menggunakan mekanisme blocklist token.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Request Body: Kosong.

Response Sukses (200 OK):

{

  "msg": "User 'username_pengguna' logged out. Harap hapus token di sisi client."

}

Response Error:

401 Unauthorized: Token tidak valid atau tidak ada.

1.2 Manajemen Gerakan (/api/gerakan)

Endpoint untuk terapis mengelola perpustakaan gerakan rehabilitasi, dan pasien melihat daftar gerakan.

1.2.1 Dapatkan Semua Gerakan

Method: GET

URL: /api/gerakan/

Deskripsi: Mendapatkan daftar semua gerakan. Mendukung paginasi dan pencarian.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Query Parameters (Opsional):

page (integer, default: 1): Halaman ke-

per_page (integer, default: 10): Jumlah item per halaman

search (string): Kata kunci pencarian berdasarkan nama gerakan

Response Sukses (200 OK):

{

  "gerakan": [

    {

      "id": 1,

      "nama_gerakan": "Angkat Kaki Lurus",

      "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",

      "url_foto": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/foto/uuid_namafile.jpg",

      "url_video": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/video/uuid_namafile.mp4",

      "url_model_tflite": "https://storage.googleapis.com/<gcs_bucket_name>/trained_tflite_models/model_uuid_namafile.tflite",

      "created_by_terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

      "created_at": "2025-06-05T11:00:00.000000",

      "updated_at": "2025-06-05T11:00:00.000000"

    }

  ],

  "total_items": 1,

  "total_pages": 1,

  "current_page": 1

}

Response Error: 401 Unauthorized.

1.2.2 Dapatkan Detail Gerakan

Method: GET

URL: /api/gerakan/<int:gerakan_id>

Deskripsi: Mendapatkan detail satu gerakan berdasarkan ID.

URL Parameters:

gerakan_id (integer, wajib): ID unik gerakan.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Response Sukses (200 OK):

{

  "id": 1,

  "nama_gerakan": "Angkat Kaki Lurus",

  "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",

  "url_foto": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/foto/uuid_namafile.jpg",

  "url_video": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/video/uuid_namafile.mp4",

  "url_model_tflite": "https://storage.googleapis.com/<gcs_bucket_name>/trained_tflite_models/model_uuid_namafile.tflite",

  "created_by_terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

  "created_at": "2025-06-05T11:00:00.000000",

  "updated_at": "2025-06-05T11:00:00.000000"

}

Response Error:

401 Unauthorized.

404 Not Found: Gerakan tidak ditemukan.

1.3 Penyajian File Media (/media/gerakan)

Endpoint ini tidak memerlukan autentikasi JWT agar file bisa diakses langsung oleh tag <img> atau <video> di frontend/mobile.

1.3.1 Sajikan Foto Gerakan

Method: GET

URL: /media/gerakan/foto/<path:filename>

Deskripsi: Mengakses file foto gerakan. filename adalah nama unik file yang disimpan (misal: uuid_namafile.jpg).

Response: File gambar.

1.3.2 Sajikan Video Gerakan

Method: GET

URL: /media/gerakan/video/<path:filename>

Deskripsi: Mengakses file video gerakan. filename adalah nama unik file yang disimpan (misal: uuid_namafile.mp4).

Response: File video.

1.3.3 Sajikan Model .tflite Gerakan

Method: GET

URL: /media/gerakan/model_tflite/<path:filename>

Deskripsi: Mengakses file model .tflite gerakan. filename adalah nama unik file yang disimpan (misal: model_uuid_namafile.tflite).

Response: File .tflite.

1.3.4 Dapatkan Detail Laporan

Method: GET

URL: /api/laporan/<int:laporan_id>

Deskripsi: Mendapatkan detail satu laporan rehabilitasi. Bisa diakses oleh pasien pemilik atau terapis yang terkait dengan program.

URL Parameters:

laporan_id (integer, wajib): ID unik laporan.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Response Sukses (200 OK):

{

  "laporan_id": 1,

  "pasien_info": { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "pasien.rajin@example.com", "role": "pasien" },

  "program_info": { "id": 1, "nama_program": "Rehabilitasi Lutut Minggu ke-2", "nama_terapis_program": "Dr. Terapis Handal" },

  "tanggal_program_direncanakan": "2025-06-12",

  "tanggal_laporan_disubmit": "2025-06-12",

  "total_waktu_rehabilitasi_string": "30:00",

  "total_waktu_rehabilitasi_detik": 1800,

  "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",

  "detail_hasil_gerakan": [

    {

      "laporan_gerakan_id": 1,

      "nama_gerakan": "Angkat Kaki Lurus",

      "jumlah_repetisi_direncanakan": 12,

      "jumlah_sempurna": 10,

      "jumlah_tidak_sempurna": 2,

      "jumlah_tidak_terdeteksi": 0,

      "waktu_aktual_per_gerakan_detik": 300

    }

    // ... detail gerakan lainnya ...

  ],

  "summary_total_hitungan": { "sempurna": 25, "tidak_sempurna": 2, "tidak_terdeteksi": 0 },

  "created_at": "2025-06-12T10:00:00.000000"

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna tidak berhak melihat laporan ini.

404 Not Found: Laporan tidak ditemukan.

1.3.5 Dapatkan Detail Program Spesifik

Method: GET

URL: /api/program/<int:program_id>

Deskripsi: Mendapatkan detail program berdasarkan ID-nya. Bisa diakses oleh terapis pembuat atau pasien penerima.

URL Parameters:

program_id (integer, wajib): ID unik program.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Response Sukses (200 OK):

{

  "msg": "Detail program berhasil diambil",

  "program": {

    "id": 1,

    "nama_program": "Rehabilitasi Lutut Minggu ke-2",

    "tanggal_program": "2025-06-12",

    "catatan_terapis": "Fokus pada penguatan quadrisep.",

    "status": "belum_dimulai",

    "terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

    "pasien": { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "pasien.rajin@example.com", "role": "pasien" },

    "list_gerakan_direncanakan": [

      // ... (data gerakan lengkap) ...

    ],

    "created_at": "2025-06-12T09:00:00.000000",

    "updated_at": "2025-06-12T09:00:00.000000",

    "laporan_terkait": null

  }

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna tidak berhak mengakses program ini.

404 Not Found: Program tidak ditemukan.

1.3.6 Update Status Program

Method: PUT

URL: /api/program/<int:program_id>/update-status

Deskripsi: Terapis atau sistem mengubah status program (misal, dari belum_dimulai ke berjalan, atau dari berjalan ke dibatalkan). Pasien juga bisa mengubah ke berjalan.

URL Parameters:

program_id (integer, wajib): ID unik program.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Content-Type: application/json

Request Body:

{

  "status": "berjalan" // Pilihan: "belum_dimulai", "berjalan", "selesai", "dibatalkan"

}

Response Sukses (200 OK):

{

  "msg": "Status program berhasil diubah menjadi 'berjalan'",

  "program": {

    "id": 1,

    "nama_program": "Rehabilitasi Lutut Minggu ke-2",

    "tanggal_program": "2025-06-12",

    "status": "berjalan"

  }

}

Response Error:

400 Bad Request: Status baru tidak disediakan atau tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna tidak berhak mengubah status ini (misal: pasien mencoba mengubah ke selesai).

404 Not Found: Program tidak ditemukan.

1.3.7 Dapatkan Summary Monitoring Pasien

Method: GET

URL: /api/monitoring/summary/pasien/<int:pasien_id>

Deskripsi: Mendapatkan data ringkasan lengkap untuk dashboard monitoring pasien (KPI, tren, distribusi hasil gerakan, catatan terbaru, dan riwayat aktivitas).

URL Parameters:

pasien_id (integer, wajib): ID unik pasien.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA> (Terapis atau Pasien pemilik)

Response Sukses (200 OK):

{

  "pasien_info": {

    "nama_lengkap": "Budi Pasien Rajin",

    "id_pasien_string": "PAS002",

    "user_id": 2,

    "jenis_kelamin": "Laki-laki",

    "tanggal_lahir": "15-05-1990",

    "diagnosis": "Post-stroke ringan, pemulihan baik",

    "catatan_tambahan_pasien": "Perlu perhatian pada gerakan motorik halus.",

    "url_foto_profil": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg",

    "total_points": 1500,

    "highest_badge_info": {

      "id": 1,

      "name": "Bintang Perunggu",

      "description": "Diberikan untuk mencapai 1000 poin.",

      "point_threshold": 1000,

      "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

      "created_at": "2025-01-01T00:00:00.000000",

      "updated_at": "2025-01-01T00:00:00.000000"

    }

  },

  "summary_kpi": {

    "total_sesi_selesai": 5,

    "rata_rata_akurasi_persen": 85,

    "rata_rata_durasi_string": "25m 30s",

    "rata_rata_durasi_detik": 1530,

    "frekuensi_latihan_per_minggu": 3.5

  },

  "trends_chart": {

    "akurasi_7_sesi_terakhir": {

      "labels": ["29 Mei", "31 Mei", "02 Jun", "04 Jun", "05 Jun"],

      "data": [80, 82, 85, 88, 90]

    },

    "durasi_7_sesi_terakhir": {

      "labels": ["29 Mei", "31 Mei", "02 Jun", "04 Jun", "05 Jun"],

      "data": [30, 28, 25, 26, 24]

    }

  },

  "distribusi_hasil_gerakan_total": {

    "labels": ["Sempurna", "Tidak Sempurna", "Tidak Terdeteksi"],

    "data": [250, 30, 15]

  },

  "catatan_observasi_terbaru": [

    {

      "tanggal": "2025-06-05",

      "catatan": "Pasien menunjukkan peningkatan signifikan minggu ini.",

      "sumber": "Terapis (Dr. Terapis Handal) - Program: Rehabilitasi Lutut Minggu ke-2"

    },

    {

      "tanggal": "2025-06-04",

      "catatan": "Latihan hari ini terasa lebih ringan.",

      "sumber": "Pasien - Laporan Program: Rehabilitasi Lutut Minggu ke-2"

    }

  ],

  "riwayat_aktivitas_monitoring": [

    {

      "tanggal_program": "2025-06-05",

      "nama_program": "Rehabilitasi Lutut Minggu ke-2",

      "status_program": "selesai",

      "laporan_id": 1,

      "keterangan_sesi": "Semua gerakan terasa baik, sedikit pegal."

    }

  ]

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna tidak berhak melihat summary ini.

404 Not Found: Pasien tidak ditemukan atau belum ada laporan yang selesai.

1.3.8 Dapatkan Leaderboard

Method: GET

URL: /api/gamification/leaderboard

Deskripsi: Endpoint untuk mendapatkan leaderboard pasien berdasarkan total poin. Dapat diakses oleh terapis dan pasien.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Query Parameters (Opsional):

page (integer, default: 1): Halaman hasil leaderboard.

per_page (integer, default: 10): Jumlah item per halaman.

Response Sukses (200 OK):

{

  "leaderboard": [

    {

      "user_id": 1,

      "username": "pasien_hebat",

      "nama_lengkap": "Pasien Hebat",

      "total_points": 2500,

      "highest_badge_info": {

        "id": 2,

        "name": "Bintang Perak",

        "description": "Diberikan untuk mencapai 2000 poin.",

        "point_threshold": 2000,

        "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/silver_star.png",

        "created_at": "2025-02-01T00:00:00.000000",

        "updated_at": "2025-02-01T00:00:00.000000"

      }

    },

    {

      "user_id": 2,

      "username": "pasien_rajin",

      "nama_lengkap": "Budi Pasien Rajin",

      "total_points": 1500,

      "highest_badge_info": {

        "id": 1,

        "name": "Bintang Perunggu",

        "description": "Diberikan untuk mencapai 1000 poin.",

        "point_threshold": 1000,

        "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

        "created_at": "2025-01-01T00:00:00.000000",

        "updated_at": "2025-01-01T00:00:00.000000"

      }

    }

  ],

  "total_items": 2,

  "total_pages": 1,

  "current_page": 1

}

Response Error: 401 Unauthorized.

1.3.9 Dapatkan Semua Badge

Method: GET

URL: /api/gamification/badges

Deskripsi: Endpoint untuk mendapatkan semua daftar badge yang tersedia. Dapat diakses oleh semua role yang terautentikasi.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Response Sukses (200 OK):

{

  "badges": [

    {

      "id": 1,

      "name": "Bintang Perunggu",

      "description": "Diberikan untuk mencapai 1000 poin.",

      "point_threshold": 1000,

      "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

      "created_at": "2025-01-01T00:00:00.000000",

      "updated_at": "2025-01-01T00:00:00.000000"

    },

    {

      "id": 2,

      "name": "Bintang Perak",

      "description": "Diberikan untuk mencapai 2000 poin.",

      "point_threshold": 2000,

      "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/silver_star.png",

      "created_at": "2025-02-01T00:00:00.000000",

      "updated_at": "2025-02-01T00:00:00.000000"

    }

  ]

}

Response Error: 401 Unauthorized.

1.3.10 Dapatkan Detail Badge

Method: GET

URL: /api/gamification/badges/<int:badge_id>

Deskripsi: Endpoint untuk mendapatkan detail badge spesifik.

URL Parameters:

badge_id (integer, wajib): ID unik badge.

Headers:

Authorization: Bearer <TOKEN_PENGGUNA>

Response Sukses (200 OK):

{

  "id": 1,

  "name": "Bintang Perunggu",

  "description": "Diberikan untuk mencapai 1000 poin.",

  "point_threshold": 1000,

  "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

  "created_at": "2025-01-01T00:00:00.000000",

  "updated_at": "2025-01-01T00:00:00.000000"

}

Response Error:

401 Unauthorized.

404 Not Found: Badge tidak ditemukan.

2\. API Khusus Pasien

Bagian ini berisi endpoint yang khusus ditujukan untuk pengguna dengan peran Pasien.

2.1 Profil Pasien (/api/patient)

Endpoint yang berkaitan dengan data profil pasien.

2.1.1 Dapatkan Profil Pasien (Saat Ini Login)

Method: GET

URL: /api/patient/profile

Deskripsi: Mendapatkan detail profil lengkap dari pasien yang sedang login.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Response Sukses (200 OK):

{

  "id": 2,

  "username": "pasien_rajin",

  "nama_lengkap": "Budi Pasien Rajin",

  "email": "pasien.rajin@example.com",

  "role": "pasien",

  "total_points": 1500,

  "jenis_kelamin": "Laki-laki",

  "tanggal_lahir": "1990-05-15",

  "tempat_lahir": "Jakarta",

  "nomor_telepon": "081234567890",

  "alamat": "Jl. Sehat No. 1",

  "nama_pendamping": "Siti Pendamping",

  "diagnosis": "Post-stroke ringan",

  "catatan_tambahan": "Perlu perhatian pada gerakan motorik halus.",

  "tinggi_badan": 170,

  "berat_badan": 65.5,

  "golongan_darah": "O+",

  "riwayat_medis": "Hipertensi terkontrol",

  "riwayat_alergi": "Tidak ada",

  "url_foto_profil": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg",

  "updated_at": "2025-06-05T10:30:00.000000",

  "highest_badge_info": {

    "id": 1,

    "name": "Bintang Perunggu",

    "description": "Diberikan untuk mencapai 1000 poin.",

    "point_threshold": 1000,

    "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

    "created_at": "2025-01-01T00:00:00.000000",

    "updated_at": "2025-01-01T00:00:00.000000"

  }

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

404 Not Found: Profil pasien tidak ditemukan.

2.1.2 Update Profil Pasien (Saat Ini Login)

Method: PUT

URL: /api/patient/profile

Deskripsi: Memperbarui detail profil pasien yang sedang login.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Content-Type: application/json

Request Body (kirim hanya field yang ingin diubah):

{

  "nama_lengkap": "Budi Pasien Semangat",

  "nomor_telepon": "08111222333",

  "alamat": "Jl. Sehat Selalu No. 12",

  "diagnosis": "Post-stroke ringan, pemulihan baik",

  "tinggi_badan": 171

}

Response Sukses (200 OK):

{

  "msg": "Profil berhasil diperbarui",

  "profile": {

    // ... (data profil lengkap yang sudah terupdate, sama seperti GET profile) ...

  }

}

Response Error:

400 Bad Request: Data tidak valid (misal format tanggal salah).

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

404 Not Found: Profil pasien tidak ditemukan.

409 Conflict: Username, email, atau nomor telepon baru sudah digunakan.

500 Internal Server Error.

2.1.3 Upload/Update Foto Profil Pasien

Method: POST atau PUT

URL: /api/patient/profile/picture

Deskripsi: Mengunggah atau memperbarui foto profil pasien.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Content-Type: multipart/form-data

Request Body: form-data

foto_profil (file, wajib): (file gambar .png, .jpg, dll.)

Response Sukses (200 OK):

{

  "msg": "Foto profil berhasil diupdate",

  "url_foto_profil": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg"

}

Response Error:

400 Bad Request: File foto_profil tidak ditemukan atau format file salah.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

404 Not Found: Profil tidak ditemukan.

500 Internal Server Error.

2.1.4 Dapatkan Rencana Pola Makan Pasien (Tanggal Spesifik)

Method: GET

URL: /api/patient/diet-plan/<string:tanggal_str>

Deskripsi: Pasien mendapatkan rencana pola makan mereka untuk tanggal tertentu.

URL Parameters:

tanggal_str (string, wajib): Tanggal dalam format YYYY-MM-DD.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Response Sukses (200 OK):

{

  "id": 1,

  "pasien_id": 2,

  "nama_pasien": "Budi Pasien Rajin",

  "terapis_id": 1,

  "nama_terapis": "Dr. Terapis Handal",

  "tanggal_makan": "2025-06-12",

  "menu_pagi": "Oatmeal dengan buah beri",

  "menu_siang": "Nasi merah, ayam bakar, sayur brokoli",

  "menu_malam": "Sup ikan, tempe kukus",

  "cemilan": "Apel, kacang almond",

  "created_at": "2025-06-12T09:00:00.000000",

  "updated_at": "2025-06-12T09:00:00.000000"

}

Response Error:

400 Bad Request: Format tanggal tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

404 Not Found: Tidak ada rencana pola makan untuk tanggal ini.

2.1.5 Dapatkan Program Rehabilitasi Pasien (Tampilan Kalender)

Method: GET

URL: /api/patient/calendar-programs

Deskripsi: Pasien mendapatkan daftar program rehabilitasi mereka untuk tampilan kalender, dengan filter berdasarkan rentang tanggal (opsional).

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Query Parameters (Opsional):

start_date (string, YYYY-MM-DD): Tanggal mulai rentang.

end_date (string, YYYY-MM-DD): Tanggal akhir rentang.

Response Sukses (200 OK):

{

  "programs": [

    {

      "id": 1,

      "nama_program": "Rehabilitasi Lutut Minggu ke-2",

      "tanggal_program": "2025-06-12",

      "status": "belum_dimulai",

      "catatan_terapis": "Fokus pada penguatan quadrisep.",

      "terapis_nama": "Dr. Terapis Handal"

    },

    {

      "id": 2,

      "nama_program": "Terapi Bahu Bulan Pertama",

      "tanggal_program": "2025-06-15",

      "status": "berjalan",

      "catatan_terapis": null,

      "terapis_nama": "Dr. Terapis Handal"

    }

  ]

}

Response Error:

400 Bad Request: Format tanggal start_date atau end_date tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

2.2 Program Rehabilitasi (/api/program)

Endpoint untuk pasien melihat programnya.

2.2.1 Dapatkan Program Hari Ini/Aktif

Method: GET

URL: /api/program/pasien/today

Deskripsi: Pasien mendapatkan program aktif yang dijadwalkan untuk hari ini atau program aktif terdekat yang belum selesai.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Response Sukses (200 OK):

{

  "id": 1,

  "nama_program": "Rehabilitasi Lutut Minggu ke-2",

  "tanggal_program": "2025-06-12",

  "catatan_terapis": "Fokus pada penguatan quadrisep.",

  "status": "belum_dimulai",

  "terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

  "pasien": { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "pasien.rajin@example.com", "role": "pasien" },

  "list_gerakan_direncanakan": [

    // ... (data gerakan lengkap) ...

  ],

  "total_planned_movements": 27,

  "estimated_total_duration_minutes": 135,

  "created_at": "2025-06-12T09:00:00.000000",

  "updated_at": "2025-06-12T09:00:00.000000",

  "laporan_terkait": null

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

404 Not Found: Jika tidak ada program aktif yang dijadwalkan.

2.2.2 Dapatkan Riwayat Program

Method: GET

URL: /api/program/pasien/history

Deskripsi: Pasien mendapatkan riwayat semua program yang pernah di-assign kepadanya (mendukung paginasi).

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Query Parameters (Opsional):

page (integer, default: 1)

per_page (integer, default: 10)

Response Sukses (200 OK):

{

  "programs": [

    {

      "id": 1,

      "nama_program": "Rehabilitasi Lutut Minggu ke-2",

      "tanggal_program": "2025-06-12",

      "catatan_terapis": "Fokus pada penguatan quadrisep.",

      "status": "belum_dimulai",

      "terapis": { /* ... */ },

      "pasien": { /* ... */ },

      "list_gerakan_direncanakan": [ /* ... */ ],

      "total_planned_movements": 27,

      "estimated_total_duration_minutes": 135,

      "created_at": "2025-06-12T09:00:00.000000",

      "updated_at": "2025-06-12T09:00:00.000000",

      "laporan_terkait": null

    }

    // ... item lainnya ...

  ],

  "total_items": 5,

  "total_pages": 1,

  "current_page": 1

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

2.3 Laporan Hasil Rehabilitasi (/api/laporan)

Endpoint untuk pasien mengirimkan hasil pelaksanaan program dan untuk melihat laporan.

2.3.1 Submit Laporan Hasil Rehabilitasi

Method: POST

URL: /api/laporan/submit

Deskripsi: Pasien mengirimkan hasil dari program rehabilitasi yang telah dilakukan.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Content-Type: application/json

Request Body:

{

  "program_rehabilitasi_id": 1, // ID program yang dilaporkan

  "tanggal_laporan": "2025-06-12", // Tanggal laporan disubmit/program dilakukan

  "total_waktu_rehabilitasi_detik": 1800, // Total waktu dalam detik

  "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",

  "detail_hasil_gerakan": [ // Array hasil per gerakan

    {

      "gerakan_id": 1, // ID gerakan dari library

      "urutan_gerakan_dalam_program": 1, // Urutan gerakan ini saat dilakukan

      "jumlah_sempurna": 10,

      "jumlah_tidak_sempurna": 2,

      "jumlah_tidak_terdeteksi": 0,

      "waktu_aktual_per_gerakan_detik": 300 // Waktu untuk gerakan ini (detik)

    },

    {

      "gerakan_id": 3,

      "urutan_gerakan_dalam_program": 2,

      "jumlah_sempurna": 15,

      "jumlah_tidak_sempurna": 0,

      "jumlah_tidak_terdeteksi": 0,

      "waktu_aktual_per_gerakan_detik": 360

    }

  ]

}

Response Sukses (201 Created):

{

  "msg": "Laporan berhasil disubmit",

  "data_laporan": {

    "laporan_id": 1,

    "pasien_info": { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "pasien.rajin@example.com", "role": "pasien" },

    "program_info": { "id": 1, "nama_program": "Rehabilitasi Lutut Minggu ke-2", "nama_terapis_program": "Dr. Terapis Handal" },

    "tanggal_program_direncanakan": "2025-06-12",

    "tanggal_laporan_disubmit": "2025-06-12",

    "total_waktu_rehabilitasi_string": "30:00",

    "total_waktu_rehabilitasi_detik": 1800,

    "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",

    "points_earned": 250,

    "detail_hasil_gerakan": [

      {

        "laporan_gerakan_id": 1,

        "nama_gerakan": "Angkat Kaki Lurus",

        "jumlah_repetisi_direncanakan": 12,

        "jumlah_sempurna": 10,

        "jumlah_tidak_sempurna": 2,

        "jumlah_tidak_terdeteksi": 0,

        "waktu_aktual_per_gerakan_detik": 300

      }

      // ... detail gerakan lainnya ...

    ],

    "summary_total_hitungan": { "sempurna": 25, "tidak_sempurna": 2, "tidak_terdeteksi": 0 },

    "created_at": "2025-06-12T10:00:00.000000"

  }

}

Response Error:

400 Bad Request: program_rehabilitasi_id atau detail_hasil_gerakan tidak ada/tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pasien tidak berhak mengirim laporan untuk program ini.

404 Not Found: Program tidak ditemukan.

409 Conflict: Laporan untuk program ini sudah pernah disubmit.

500 Internal Server Error.

2.3.2 Dapatkan Riwayat Laporan

Method: GET

URL: /api/laporan/pasien/history

Deskripsi: Pasien mendapatkan daftar semua laporannya (mendukung paginasi).

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Query Parameters (Opsional):

page (integer, default: 1)

per_page (integer, default: 10)

Response Sukses (200 OK):

{

  "laporan": [

    {

      "laporan_id": 1,

      "pasien_info": { /* ... */ },

      "program_info": { /* ... */ },

      "tanggal_program_direncanakan": "2025-06-12",

      "tanggal_laporan_disubmit": "2025-06-12",

      "total_waktu_rehabilitasi_string": "30:00",

      "total_waktu_rehabilitasi_detik": 1800,

      "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",

      "points_earned": 250,

      "detail_hasil_gerakan": [ /* ... */ ],

      "summary_total_hitungan": { /* ... */ },

      "created_at": "2025-06-12T10:00:00.000000"

    }

    // ... daftar laporan ...

  ],

  "total_items": 3,

  "total_pages": 1,

  "current_page": 1

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

2.4 Gamifikasi (/api/gamification)

Endpoint untuk pasien melihat badge yang mereka dapatkan.

2.4.1 Dapatkan Badge Saya

Method: GET

URL: /api/gamification/my-badges

Deskripsi: Endpoint untuk pasien melihat daftar badge yang sudah mereka dapatkan.

Headers:

Authorization: Bearer <TOKEN_PASIEN>

Response Sukses (200 OK):

{

  "my_badges": [

    {

      "id": 1,

      "user_id": 2,

      "badge_info": {

        "id": 1,

        "name": "Bintang Perunggu",

        "description": "Diberikan untuk mencapai 1000 poin.",

        "point_threshold": 1000,

        "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

        "created_at": "2025-01-01T00:00:00.000000",

        "updated_at": "2025-01-01T00:00:00.000000"

      },

      "awarded_at": "2025-06-15T11:00:00.000000"

    }

  ]

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan pasien.

3\. API Khusus Terapis

Bagian ini berisi endpoint yang khusus ditujukan untuk pengguna dengan peran Terapis.

3.1 Manajemen Gerakan (/api/gerakan)

Endpoint untuk terapis mengelola perpustakaan gerakan rehabilitasi.

3.1.1 Buat Gerakan Baru

Method: POST

URL: /api/gerakan/

Deskripsi: Terapis menambahkan gerakan baru ke perpustakaan.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: multipart/form-data (akan otomatis jika mengirim file)

Request Body: form-data

nama_gerakan (teks, wajib): "Angkat Kaki Lurus"

deskripsi (teks, opsional): "Berbaring, angkat satu kaki lurus ke atas."

foto (file, opsional): (file gambar .png, .jpg, dll.)

video (file, opsional): (file video .mp4, .mov, dll.)

model_tflite (file, opsional): (file .tflite)

Response Sukses (201 Created):

{

  "msg": "Gerakan berhasil dibuat",

  "gerakan": {

    "id": 1,

    "nama_gerakan": "Angkat Kaki Lurus",

    "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",

    "url_foto": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/foto/uuid_namafile.jpg",

    "url_video": "https://<azure_storage_account>.blob.core.windows.net/<container>/gerakan/video/uuid_namafile.mp4",

    "url_model_tflite": "https://storage.googleapis.com/<gcs_bucket_name>/trained_tflite_models/model_uuid_namafile.tflite",

    "created_by_terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

    "created_at": "2025-06-05T11:00:00.000000",

    "updated_at": "2025-06-05T11:00:00.000000"

  }

}

Response Error:

400 Bad Request: Data form tidak lengkap, format file salah, atau error upload.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

500 Internal Server Error.

3.1.2 Update Gerakan

Method: PUT

URL: /api/gerakan/<int:gerakan_id>

Deskripsi: Terapis memperbarui detail gerakan.

URL Parameters:

gerakan_id (integer, wajib): ID unik gerakan.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: multipart/form-data

Request Body: form-data (kirim field yang ingin diubah, termasuk file jika ingin mengganti)

nama_gerakan (teks, opsional)

deskripsi (teks, opsional)

foto (file, opsional)

video (file, opsional)

model_tflite (file, opsional)

Response Sukses (200 OK):

{

  "msg": "Gerakan berhasil diupdate",

  "gerakan": {

    // ... (data gerakan lengkap yang sudah terupdate, sama seperti GET detail gerakan) ...

  }

}

Response Error:

400 Bad Request: Data form tidak lengkap, format file salah, atau error upload.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Gerakan tidak ditemukan.

500 Internal Server Error.

3.1.3 Hapus Gerakan

Method: DELETE

URL: /api/gerakan/<int:gerakan_id>

Deskripsi: Terapis menghapus gerakan dari perpustakaan.

URL Parameters:

gerakan_id (integer, wajib): ID unik gerakan.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "msg": "Gerakan berhasil dihapus"

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Gerakan tidak ditemukan.

500 Internal Server Error.

3.2 Program Rehabilitasi (/api/program)

Endpoint untuk terapis membuat dan meng-assign program.

3.2.1 Dapatkan Daftar Pasien

Method: GET

URL: /api/program/pasien-list

Deskripsi: Terapis mendapatkan daftar semua pasien untuk dipilih saat membuat program, termasuk URL foto profil dan diagnosis pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

[

  {

    "id": 2,

    "username": "pasien_rajin",

    "nama_lengkap": "Budi Pasien Rajin",

    "email": "pasien.rajin@example.com",

    "role": "pasien",

    "total_points": 1500,

    "foto_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg",

    "diagnosis": "Post-stroke ringan"

  },

  {

    "id": 3,

    "username": "siti_pasien",

    "nama_lengkap": "Siti Pasien",

    "email": "siti.pasien@example.com",

    "role": "pasien",

    "total_points": 500,

    "foto_url": null,

    "diagnosis": "Belum ada diagnosis"

  }

]

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

3.2.2 Dapatkan Informasi Pasien untuk Konteks Program

Method: GET

URL: /api/program/patient-info/<int:pasien_id>

Deskripsi: Terapis mendapatkan informasi dasar pasien (termasuk foto, diagnosis, jenis kelamin, tanggal lahir, dan total poin) dalam konteks modul program.

URL Parameters:

pasien_id (integer, wajib): ID unik pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "id": 2,

  "username": "pasien_rajin",

  "nama_lengkap": "Budi Pasien Rajin",

  "email": "pasien.rajin@example.com",

  "role": "pasien",

  "total_points": 1500,

  "foto_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg",

  "diagnosis": "Post-stroke ringan",

  "jenis_kelamin": "Laki-laki",

  "tanggal_lahir": "1990-05-15"

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pasien tidak ditemukan.

3.2.3 Buat & Assign Program Baru

Method: POST

URL: /api/program/

Deskripsi: Terapis membuat program baru dan meng-assign ke pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: application/json

Request Body:

{

  "nama_program": "Rehabilitasi Lutut Minggu ke-2",

  "pasien_id": 2, // ID pasien yang dituju

  "tanggal_program": "2025-06-12", // Tanggal program ini akan dilakukan pasien

  "catatan_terapis": "Fokus pada penguatan quadrisep.",

  "status": "belum_dimulai", // Opsional, default: belum_dimulai

  "list_gerakan_direncanakan": [

    { "gerakan_id": 1, "jumlah_repetisi_direncanakan": 12, "urutan_dalam_program": 1 },

    { "gerakan_id": 3, "jumlah_repetisi_direncanakan": 15, "urutan_dalam_program": 2 }

  ]

}

Response Sukses (201 Created):

{

  "msg": "Program rehabilitasi berhasil dibuat dan di-assign",

  "program": {

    "id": 1,

    "nama_program": "Rehabilitasi Lutut Minggu ke-2",

    "tanggal_program": "2025-06-12",

    "catatan_terapis": "Fokus pada penguatan quadrisep.",

    "status": "belum_dimulai",

    "terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

    "pasien": { "id": 2, "username": "pasien_rajin", "nama_lengkap": "Budi Pasien Rajin", "email": "pasien.rajin@example.com", "role": "pasien" },

    "list_gerakan_direncanakan": [

      {

        "id": 1,

        "nama_gerakan": "Angkat Kaki Lurus",

        "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",

        "url_foto": "...",

        "url_video": "...",

        "url_model_tflite": "...",

        "created_by_terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

        "created_at": "...",

        "updated_at": "...",

        "jumlah_repetisi_direncanakan": 12,

        "urutan_dalam_program": 1,

        "program_gerakan_detail_id": 1

      }

      // ... gerakan lainnya ...

    ],

    "total_planned_movements": 27,

    "estimated_total_duration_minutes": 135,

    "created_at": "2025-06-12T09:00:00.000000",

    "updated_at": "2025-06-12T09:00:00.000000",

    "laporan_terkait": null

  }

}

Response Error:

400 Bad Request: Data tidak lengkap, format tanggal/status tidak valid, atau data gerakan tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pasien atau gerakan tidak ditemukan.

500 Internal Server Error.

3.2.4 Dapatkan Program yang Di-assign ke Pasien Tertentu

Method: GET

URL: /api/program/terapis/assigned-to-patient/<int:pasien_id>

Deskripsi: Terapis mendapatkan riwayat program yang telah ia assign ke pasien tertentu (mendukung paginasi).

URL Parameters:

pasien_id (integer, wajib): ID unik pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Query Parameters (Opsional):

page (integer, default: 1)

per_page (integer, default: 100)

Response Sukses (200 OK):

{

  "msg": "Daftar program yang di-assign ke pasien NAMA_PASIEN berhasil diambil",

  "programs": [

    {

      "id": 1,

      "nama_program": "Rehabilitasi Lutut Minggu ke-2",

      "tanggal_program": "2025-06-12",

      "catatan_terapis": "Fokus pada penguatan quadrisep.",

      "status": "belum_dimulai",

      "terapis": { /* ... */ },

      "pasien": { /* ... */ },

      "list_gerakan_direncanakan": [ /* ... */ ],

      "total_planned_movements": 27,

      "estimated_total_duration_minutes": 135,

      "created_at": "2025-06-12T09:00:00.000000",

      "updated_at": "2025-06-12T09:00:00.000000",

      "laporan_terkait": null

    }

    // ... daftar program ...

  ],

  "total_items": 5,

  "total_pages": 1,

  "current_page": 1

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pasien tidak ditemukan.

3.3 Laporan Hasil Rehabilitasi (/api/laporan)

Endpoint untuk terapis melihat laporan.

3.3.1 Dapatkan Riwayat Laporan Pasien Tertentu

Method: GET

URL: /api/laporan/terapis/by-pasien/<int:target_pasien_id>

Deskripsi: Terapis mendapatkan daftar laporan dari pasien tertentu yang pernah di-assign program olehnya (mendukung paginasi).

URL Parameters:

target_pasien_id (integer, wajib): ID unik pasien target.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Query Parameters (Opsional):

page (integer, default: 1)

per_page (integer, default: 10)

Response Sukses (200 OK):

{

  "msg": "Riwayat laporan untuk pasien NAMA_PASIEN berhasil diambil",

  "laporan": [

    {

      "laporan_id": 1,

      "pasien_info": { /* ... */ },

      "program_info": { /* ... */ },

      "tanggal_program_direncanakan": "2025-06-12",

      "tanggal_laporan_disubmit": "2025-06-12",

      "total_waktu_rehabilitasi_string": "30:00",

      "total_waktu_rehabilitasi_detik": 1800,

      "catatan_pasien_laporan": "Semua gerakan terasa baik, sedikit pegal.",

      "points_earned": 250,

      "detail_hasil_gerakan": [ /* ... */ ],

      "summary_total_hitungan": { /* ... */ },

      "created_at": "2025-06-12T10:00:00.000000"

    }

    // ... daftar laporan ...

  ],

  "total_items": 3,

  "total_pages": 1,

  "current_page": 1

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna tidak berhak melihat laporan pasien ini.

404 Not Found: Pasien tidak ditemukan.

3.4 Manajemen Pola Makan oleh Terapis (/api/terapis)

Endpoint khusus untuk terapis mengelola pola makan pasien.

3.4.1 Dapatkan Detail Pasien Saya

Method: GET

URL: /api/terapis/my-patients-details

Deskripsi: Terapis mendapatkan daftar detail pasien yang pernah mereka tangani, termasuk URL foto profil dan diagnosis pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "patients": [

    {

      "id": 2,

      "nama": "Budi Pasien Rajin",

      "email": "pasien.rajin@example.com",

      "foto_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/profil/foto/uuid_namafile.jpg",

      "diagnosis": "Post-stroke ringan"

    },

    {

      "id": 3,

      "nama": "Siti Pasien",

      "email": "siti.pasien@example.com",

      "foto_url": null,

      "diagnosis": "Belum ada diagnosis"

    }

  ]

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

3.4.2 Dapatkan Ringkasan Dashboard

Method: GET

URL: /api/terapis/dashboard-summary

Deskripsi: Mendapatkan data ringkasan KPI dan data grafik untuk dashboard terapis.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "kpi": {

    "total_pasien_ditangani": 10,

    "pasien_rehabilitasi_hari_ini": 3,

    "pasien_selesai_rehabilitasi_hari_ini": 1

  },

  "program_terbaru_terapis": [

    {

      "id": 5,

      "program_name": "Rehabilitasi Kaki Kiri Lanjutan",

      "patient_id": 2,

      "patient_name": "Budi Pasien Rajin",

      "execution_date": "2025-06-12",

      "status": "berjalan",

      "catatan_terapis": "Fokus pada kekuatan sendi.",

      "movements_details": [

        {

          "id": 1,

          "nama_gerakan": "Angkat Kaki Lurus",

          "deskripsi": "Berbaring, angkat satu kaki lurus ke atas.",

          "url_foto": "...",

          "url_video": "...",

          "url_model_tflite": "...",

          "created_by_terapis": { "id": 1, "username": "terapis_handal", "nama_lengkap": "Dr. Terapis Handal", "email": "terapis.handal@example.com", "role": "terapis" },

          "created_at": "...",

          "updated_at": "...",

          "jumlah_repetisi_direncanakan": 12,

          "urutan_dalam_program": 1,

          "program_gerakan_detail_id": 1

        }

      ]

    },

    {

      "id": 4,

      "program_name": "Terapi Pergelangan Tangan",

      "patient_id": 3,

      "patient_name": "Siti Pasien",

      "execution_date": "2025-06-10",

      "status": "selesai",

      "catatan_terapis": null,

      "movements_details": [ /* ... */ ]

    }

  ],

  "chart_data_patients_per_day": {

    "labels": ["13 Mei", "14 Mei", "15 Mei", "...", "12 Jun"],

    "data": [0, 1, 0, /* ... */, 1] // Jumlah pasien baru yang di-assign setiap hari

  }

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

3.4.3 Buat Rencana Pola Makan

Method: POST

URL: /api/terapis/diet-plan

Deskripsi: Terapis membuat rencana pola makan baru untuk pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: application/json

Request Body:

{

  "pasien_id": 2,

  "tanggal_makan": "2025-06-12",

  "menu_pagi": "Roti gandum, telur rebus",

  "menu_siang": "Salad sayuran, dada ayam panggang",

  "menu_malam": "Ikan kukus, sup brokoli",

  "cemilan": "Buah pir, yoghurt"

}

Response Sukses (201 Created):

{

  "msg": "Pola makan berhasil dibuat",

  "pola_makan": {

    "id": 1,

    "pasien_id": 2,

    "nama_pasien": "Budi Pasien Rajin",

    "terapis_id": 1,

    "nama_terapis": "Dr. Terapis Handal",

    "tanggal_makan": "2025-06-12",

    "menu_pagi": "Roti gandum, telur rebus",

    "menu_siang": "Salad sayuran, dada ayam panggang",

    "menu_malam": "Ikan kukus, sup brokoli",

    "cemilan": "Buah pir, yoghurt",

    "created_at": "2025-06-12T14:00:00.000000",

    "updated_at": "2025-06-12T14:00:00.000000"

  }

}

Response Error:

400 Bad Request: ID Pasien atau Tanggal Makan tidak diisi, atau format tanggal tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pasien tidak ditemukan.

409 Conflict: Pola makan untuk pasien dan tanggal ini sudah ada.

500 Internal Server Error.

3.4.4 Perbarui Rencana Pola Makan

Method: PUT

URL: /api/terapis/diet-plan/<int:plan_id>

Deskripsi: Terapis memperbarui rencana pola makan pasien.

URL Parameters:

plan_id (integer, wajib): ID unik rencana pola makan.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: application/json

Request Body:

{

  "menu_pagi": "Roti gandum, telur dadar",

  "cemilan": "Buah pisang"

}

Response Sukses (200 OK):

{

  "msg": "Pola makan berhasil diperbarui",

  "pola_makan": {

    "id": 1,

    "pasien_id": 2,

    "nama_pasien": "Budi Pasien Rajin",

    "terapis_id": 1,

    "nama_terapis": "Dr. Terapis Handal",

    "tanggal_makan": "2025-06-12",

    "menu_pagi": "Roti gandum, telur dadar",

    "menu_siang": "Salad sayuran, dada ayam panggang",

    "menu_malam": "Ikan kukus, sup brokoli",

    "cemilan": "Buah pisang",

    "created_at": "2025-06-12T14:00:00.000000",

    "updated_at": "2025-06-12T14:30:00.000000"

  }

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pola makan tidak ditemukan atau terapis tidak berhak mengeditnya.

500 Internal Server Error.

3.4.5 Hapus Rencana Pola Makan

Method: DELETE

URL: /api/terapis/diet-plan/<int:plan_id>

Deskripsi: Terapis menghapus rencana pola makan pasien.

URL Parameters:

plan_id (integer, wajib): ID unik rencana pola makan.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "msg": "Pola makan berhasil dihapus"

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pola makan tidak ditemukan atau terapis tidak berhak menghapusnya.

500 Internal Server Error.

3.4.6 Dapatkan Pola Makan Pasien pada Tanggal Tertentu

Method: GET

URL: /api/terapis/diet-plan/patient/<int:pasien_id>/<string:tanggal_str>

Deskripsi: Terapis mendapatkan pola makan spesifik untuk pasien dan tanggal tertentu.

URL Parameters:

pasien_id (integer, wajib): ID unik pasien.

tanggal_str (string, wajib): Tanggal dalam format YYYY-MM-DD.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "id": 1,

  "pasien_id": 2,

  "nama_pasien": "Budi Pasien Rajin",

  "terapis_id": 1,

  "nama_terapis": "Dr. Terapis Handal",

  "tanggal_makan": "2025-06-12",

  "menu_pagi": "Roti gandum, telur dadar",

  "menu_siang": "Salad sayuran, dada ayam panggang",

  "menu_malam": "Ikan kukus, sup brokoli",

  "cemilan": "Buah pisang",

  "created_at": "2025-06-12T14:00:00.000000",

  "updated_at": "2025-06-12T14:30:00.000000"

}

Response Error:

400 Bad Request: Format tanggal tidak valid.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Pola makan tidak ditemukan untuk pasien dan tanggal tersebut.

3.4.7 Dapatkan Semua Pola Makan untuk Pasien Tertentu

Method: GET

URL: /api/terapis/diet-plan/patient/<int:pasien_id>/all

Deskripsi: Terapis mendapatkan daftar semua rencana pola makan untuk pasien tertentu.

URL Parameters:

pasien_id (integer, wajib): ID unik pasien.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "pola_makan": [

    {

      "id": 1,

      "pasien_id": 2,

      "nama_pasien": "Budi Pasien Rajin",

      "terapis_id": 1,

      "nama_terapis": "Dr. Terapis Handal",

      "tanggal_makan": "2025-06-12",

      "menu_pagi": "Roti gandum, telur dadar",

      "menu_siang": "Salad sayuran, dada ayam panggang",

      "menu_malam": "Ikan kukus, sup brokoli",

      "cemilan": "Buah pisang",

      "created_at": "2025-06-12T14:00:00.000000",

      "updated_at": "2025-06-12T14:30:00.000000"

    },

    {

      "id": 2,

      "pasien_id": 2,

      "nama_pasien": "Budi Pasien Rajin",

      "terapis_id": 1,

      "nama_terapis": "Dr. Terapis Handal",

      "tanggal_makan": "2025-06-11",

      "menu_pagi": "Nasi goreng",

      "menu_siang": "Mie ayam",

      "menu_malam": "Sate ayam",

      "cemilan": "Keripik"

    }

  ]

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

3.5 Gamifikasi (/api/gamification)

Endpoint untuk terapis mengelola badge.

3.5.1 Buat Badge Baru

Method: POST

URL: /api/gamification/badges

Deskripsi: Endpoint untuk terapis membuat badge baru. Membutuhkan nama, deskripsi, ambang batas poin, dan file gambar.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: multipart/form-data

Request Body: form-data

name (teks, wajib): "Bintang Perunggu"

description (teks, opsional): "Diberikan untuk mencapai 1000 poin."

point_threshold (integer, wajib): 1000

image (file, wajib): (file gambar .png, .jpg, dll.)

Response Sukses (201 Created):

{

  "msg": "Badge berhasil dibuat",

  "badge": {

    "id": 1,

    "name": "Bintang Perunggu",

    "description": "Diberikan untuk mencapai 1000 poin.",

    "point_threshold": 1000,

    "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star.png",

    "created_at": "2025-01-01T00:00:00.000000",

    "updated_at": "2025-01-01T00:00:00.000000"

  }

}

Response Error:

400 Bad Request: Data tidak lengkap, format ambang batas poin salah, atau file gambar tidak ditemukan.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

409 Conflict: Nama badge atau ambang batas poin sudah ada.

500 Internal Server Error.

3.5.2 Perbarui Badge

Method: PUT

URL: /api/gamification/badges/<int:badge_id>

Deskripsi: Endpoint untuk terapis memperbarui detail badge yang sudah ada. Memungkinkan perubahan nama, deskripsi, ambang batas poin, dan gambar.

URL Parameters:

badge_id (integer, wajib): ID unik badge.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Content-Type: multipart/form-data

Request Body: form-data (kirim field yang ingin diubah, termasuk file jika ingin mengganti)

name (teks, opsional)

description (teks, opsional)

point_threshold (integer, opsional)

image (file, opsional)

Response Sukses (200 OK):

{

  "msg": "Badge berhasil diperbarui",

  "badge": {

    "id": 1,

    "name": "Bintang Perunggu",

    "description": "Diberikan untuk mencapai 1000 poin (Diperbarui).",

    "point_threshold": 1000,

    "image_url": "https://<azure_storage_account>.blob.core.windows.net/<container>/badges/bronze_star_updated.png",

    "created_at": "2025-01-01T00:00:00.000000",

    "updated_at": "2025-06-15T10:00:00.000000"

  }

}

Response Error:

400 Bad Request: Format ambang batas poin salah.

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Badge tidak ditemukan.

409 Conflict: Nama badge atau ambang batas poin sudah ada (jika diubah).

500 Internal Server Error.

3.5.3 Hapus Badge

Method: DELETE

URL: /api/gamification/badges/<int:badge_id>

Deskripsi: Endpoint untuk terapis menghapus badge.

URL Parameters:

badge_id (integer, wajib): ID unik badge.

Headers:

Authorization: Bearer <TOKEN_TERAPIS>

Response Sukses (200 OK):

{

  "msg": "Badge berhasil dihapus"

}

Response Error:

401 Unauthorized: Token tidak valid.

403 Forbidden: Pengguna bukan terapis.

404 Not Found: Badge tidak ditemukan.

500 Internal Server Error.
