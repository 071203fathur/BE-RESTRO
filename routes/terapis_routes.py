# BE-RESTRO/routes/terapis_routes.py

from flask import Blueprint, jsonify, current_app
from models import db, User, PatientProfile, ProgramRehabilitasi, ProgramStatus, LaporanRehabilitasi # Pastikan semua model diimport
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, distinct, extract, cast, Date as SQLDate # Untuk query agregat dan tanggal
from datetime import date, timedelta, datetime

terapis_bp = Blueprint('terapis_bp', __name__) # Nama blueprint harus unik

@terapis_bp.route('/my-patients-details', methods=['GET'])
@jwt_required()
def get_my_patients_details():
    """
    Endpoint untuk terapis mendapatkan daftar pasien yang pernah mereka tangani (pernah di-assign program).
    Mengembalikan detail dasar pasien termasuk diagnosis.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang dapat mengakses daftar pasien ini."}), 403
    
    terapis_id = current_user_identity.get('id')

    # Dapatkan semua pasien_id unik dari ProgramRehabilitasi yang di-assign oleh terapis ini
    assigned_patients_query = db.session.query(
        User.id,
        User.nama_lengkap,
        User.email, # Opsional
        PatientProfile.diagnosis,
        PatientProfile.filename_foto_profil # Asumsi Anda menambahkan field ini di PatientProfile
                                            # Jika tidak, ganti dengan None atau path default
    ).join(PatientProfile, User.id == PatientProfile.user_id)\
     .join(ProgramRehabilitasi, User.id == ProgramRehabilitasi.pasien_id)\
     .filter(ProgramRehabilitasi.terapis_id == terapis_id)\
     .distinct(User.id) # Hanya satu entri per pasien

    # Eksekusi query dan format hasilnya
    patients_details_from_db = assigned_patients_query.all()
    
    patients_list = []
    for p_data in patients_details_from_db:
        # Asumsi Anda punya cara untuk membangun URL foto profil di PatientProfile.serialize()
        # atau Anda bisa membangunnya di sini jika filename_foto_profil ada
        # Untuk sekarang, kita buat placeholder jika tidak ada
        foto_url = None
        if p_data.filename_foto_profil:
             # Ini adalah contoh, sesuaikan dengan cara Anda menyajikan file di app.py
            base_media_url = current_app.config.get('MEDIA_BASE_URL_PROFIL', '/media/profil/foto') 
            foto_url = f"{base_media_url}/{p_data.filename_foto_profil}"

        patients_list.append({
            "id": p_data.id,
            "nama": p_data.nama_lengkap,
            "email": p_data.email,
            "foto_url": foto_url, # URL lengkap ke foto profil
            "diagnosis": p_data.diagnosis if p_data.diagnosis else "Belum ada diagnosis"
        })

    if not patients_list:
        return jsonify({"msg": "Anda belum menangani pasien.", "patients": []}), 200

    return jsonify({"msg": "Daftar pasien berhasil diambil", "patients": patients_list}), 200


@terapis_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def get_terapis_dashboard_summary():
    """
    Endpoint untuk menyediakan data agregat untuk dashboard terapis.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang dapat mengakses summary ini."}), 403
    
    terapis_id = current_user_identity.get('id')
    today = date.today()

    # 1. Total Pasien Ditangani (oleh terapis ini - pasien unik yang pernah diberi program)
    total_pasien_ditangani_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
                                             .filter(ProgramRehabilitasi.terapis_id == terapis_id)\
                                             .scalar() or 0

    # 2. Pasien Rehabilitasi Hari Ini (program berjalan, dijadwalkan hari ini, oleh terapis ini)
    pasien_rehab_today_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
                                          .filter(ProgramRehabilitasi.terapis_id == terapis_id,
                                                  ProgramRehabilitasi.tanggal_program == today,
                                                  ProgramRehabilitasi.status == ProgramStatus.BERJALAN)\
                                          .scalar() or 0
    
    # 3. Pasien Selesai Rehabilitasi (memiliki setidaknya satu program berstatus 'selesai' dari terapis ini)
    pasien_selesai_rehab_ids = db.session.query(distinct(ProgramRehabilitasi.pasien_id))\
                                           .filter(ProgramRehabilitasi.terapis_id == terapis_id,
                                                   ProgramRehabilitasi.status == ProgramStatus.SELESAI)\
                                           .all()
    pasien_selesai_rehab_count = len(pasien_selesai_rehab_ids)

    # 4. Dua Program Kegiatan Terbaru yang di-assign oleh terapis ini
    program_terbaru_query = ProgramRehabilitasi.query.filter_by(terapis_id=terapis_id)\
                                                 .order_by(ProgramRehabilitasi.created_at.desc())\
                                                 .limit(2).all()
    program_terbaru_serialized = [p.serialize_full(current_app.config) for p in program_terbaru_query]

    # 5. Statistik Pasien: Jumlah pasien yang pertama kali ditangani terapis ini per bulan (6 bulan terakhir)
    six_months_ago_date = today - timedelta(days=6*30) # Perkiraan

    # Subquery untuk mendapatkan tanggal pertama kali pasien di-assign program OLEH TERAPIS INI
    first_assignment_by_this_therapist_sq = db.session.query(
        ProgramRehabilitasi.pasien_id,
        func.min(cast(ProgramRehabilitasi.created_at, SQLDate)).label('first_handled_date') # Cast ke Date untuk grouping
    ).filter(ProgramRehabilitasi.terapis_id == terapis_id)\
     .group_by(ProgramRehabilitasi.pasien_id).subquery()

    # Query utama untuk menghitung pasien baru per bulan berdasarkan tanggal penanganan pertama
    new_patients_per_month_raw = db.session.query(
        extract('year', first_assignment_by_this_therapist_sq.c.first_handled_date).label('year'),
        extract('month', first_assignment_by_this_therapist_sq.c.first_handled_date).label('month'),
        func.count(first_assignment_by_this_therapist_sq.c.pasien_id).label('new_patients_count')
    ).filter(first_assignment_by_this_therapist_sq.c.first_handled_date >= six_months_ago_date)\
     .group_by('year', 'month')\
     .order_by('year', 'month').all()
    
    statistik_pasien_labels = []
    statistik_pasien_data = []
    
    # Inisialisasi data untuk 6 bulan terakhir (termasuk bulan ini) agar semua bulan ada
    month_year_data_map = {}
    for i in range(5, -1, -1): # Dari 5 bulan lalu hingga bulan ini
        current_month_loop = today - timedelta(days=i*30) # Perkiraan kasar, lebih baik pakai library tanggal jika perlu presisi tinggi
        month_year_key = current_month_loop.strftime("%Y-%m") # Format Kunci: "2025-06"
        month_year_data_map[month_year_key] = 0
        
    for row in new_patients_per_month_raw:
        year, month, count = int(row.year), int(row.month), row.new_patients_count
        month_year_key = f"{year}-{month:02d}"
        if month_year_key in month_year_data_map:
             month_year_data_map[month_year_key] = count
    
    # Urutkan map berdasarkan kunci (tahun-bulan) untuk label dan data yang benar
    for ym_key, count in sorted(month_year_data_map.items()):
        dt_obj = datetime.strptime(ym_key, "%Y-%m")
        statistik_pasien_labels.append(dt_obj.strftime("%b")) # Format "Jan", "Feb", dst.
        statistik_pasien_data.append(count)

    # Total pasien keseluruhan dalam sistem (sebagai referensi, jika dibutuhkan UI)
    total_pasien_sistem_count = User.query.filter_by(role='pasien').count()

    dashboard_data = {
        "kpi": {
            "total_pasien_ditangani_terapis": total_pasien_ditangani_count,
            "pasien_rehabilitasi_hari_ini": pasien_rehab_today_count,
            "pasien_selesai_rehabilitasi_terapis": pasien_selesai_rehab_count # Pasien yg programnya selesai dari terapis ini
        },
        "program_terbaru_terapis": program_terbaru_serialized,
        "statistik_pasien_baru_bulanan_terapis": { # Statistik pasien baru yg ditangani terapis ini
            "labels": statistik_pasien_labels, 
            "data": statistik_pasien_data      
        },
        "referensi_total_pasien_sistem": total_pasien_sistem_count # Total semua pasien di sistem
    }

    return jsonify(dashboard_data), 200
