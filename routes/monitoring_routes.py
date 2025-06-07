# BE-RESTRO/routes/monitoring_routes.py

from flask import Blueprint, jsonify, current_app
from models import db, AppUser, PatientProfile, LaporanRehabilitasi, LaporanGerakanHasil, ProgramRehabilitasi, ProgramStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, cast, Date as SQLDate # Import SQLDate untuk casting
from datetime import date, timedelta, datetime

monitoring_bp = Blueprint('monitoring_bp', __name__)

def format_durasi_ringkas(total_detik):
    if total_detik is None or not isinstance(total_detik, (int, float)) or total_detik < 0:
        return "0m 0s"
    menit = int(total_detik // 60)
    detik = int(total_detik % 60)
    return f"{menit}m {detik}s"

@monitoring_bp.route('/summary/pasien/<int:pasien_id>', methods=['GET']) # URL lebih spesifik
@jwt_required()
def get_pasien_monitoring_summary(pasien_id): # Nama fungsi lebih spesifik
    current_user_identity = get_jwt_identity()
    user_role = current_user_identity.get('role')
    requesting_user_id = current_user_identity.get('id')
    
    pasien = AppUser.query.get(pasien_id)
    if not pasien or pasien.role != 'pasien':
        return jsonify({"msg": f"Pasien dengan ID {pasien_id} tidak ditemukan."}), 404

    # Otorisasi: Pasien hanya bisa lihat summary dirinya, Terapis bisa lihat summary pasiennya.
    # Perlu ada logika untuk menentukan apakah terapis ini berhak melihat data pasien ini.
    # Untuk sekarang, kita asumsikan terapis punya akses ke semua pasien (bisa diperketat).
    if user_role == 'pasien' and requesting_user_id != pasien_id:
        return jsonify({"msg": "Akses ditolak: Anda hanya bisa melihat summary Anda sendiri."}), 403
    
    # Ambil semua laporan yang status programnya SELESAI untuk pasien ini
    # (karena laporan dibuat setelah program selesai)
    semua_laporan_selesai = LaporanRehabilitasi.query\
                                .join(ProgramRehabilitasi, LaporanRehabilitasi.program_rehabilitasi_id == ProgramRehabilitasi.id)\
                                .filter(LaporanRehabilitasi.pasien_id == pasien_id, ProgramRehabilitasi.status == ProgramStatus.SELESAI)\
                                .order_by(LaporanRehabilitasi.tanggal_laporan.asc()).all()

    # --- 1. KPI Cards ---
    total_sesi_selesai = len(semua_laporan_selesai)
    
    rata_rata_durasi_detik = 0
    if total_sesi_selesai > 0:
        total_durasi_valid_detik = sum(filter(None, [l.total_waktu_rehabilitasi_detik for l in semua_laporan_selesai if l.total_waktu_rehabilitasi_detik is not None]))
        jumlah_sesi_dengan_durasi = sum(1 for l in semua_laporan_selesai if l.total_waktu_rehabilitasi_detik is not None)
        if jumlah_sesi_dengan_durasi > 0:
            rata_rata_durasi_detik = total_durasi_valid_detik / jumlah_sesi_dengan_durasi
    
    total_akurasi_kumulatif = 0
    jumlah_sesi_dinilai_akurasi = 0
    for laporan in semua_laporan_selesai:
        hasil_detail_sesi = LaporanGerakanHasil.query.filter_by(laporan_rehabilitasi_id=laporan.id).all()
        if hasil_detail_sesi: # Hanya jika ada detail gerakan dalam laporan
            total_gerakan_dilakukan_sesi = sum((h.jumlah_sempurna or 0) + (h.jumlah_tidak_sempurna or 0) + (h.jumlah_tidak_terdeteksi or 0) for h in hasil_detail_sesi)
            total_sempurna_sesi = sum(h.jumlah_sempurna or 0 for h in hasil_detail_sesi)
            if total_gerakan_dilakukan_sesi > 0:
                akurasi_sesi = (total_sempurna_sesi / total_gerakan_dilakukan_sesi) * 100
                total_akurasi_kumulatif += akurasi_sesi
                jumlah_sesi_dinilai_akurasi += 1
    rata_rata_akurasi_keseluruhan = total_akurasi_kumulatif / jumlah_sesi_dinilai_akurasi if jumlah_sesi_dinilai_akurasi > 0 else 0
    
    frekuensi_latihan = 0
    if total_sesi_selesai > 1:
        tanggal_pertama = semua_laporan_selesai[0].tanggal_laporan
        tanggal_terakhir = semua_laporan_selesai[-1].tanggal_laporan
        if tanggal_pertama and tanggal_terakhir: # Pastikan tanggal tidak None
            rentang_hari = (tanggal_terakhir - tanggal_pertama).days
            if rentang_hari >= 0 : # Rentang hari bisa 0 jika hanya 1 sesi pada hari yang sama
                rentang_minggu = (rentang_hari / 7.0) if rentang_hari > 0 else (1/7.0) # Anggap 1 sesi = 1/7 minggu
                frekuensi_latihan = total_sesi_selesai / rentang_minggu if rentang_minggu > 0 else total_sesi_selesai * 7 # Jika dalam 1 hari
    elif total_sesi_selesai == 1:
        frekuensi_latihan = 1 # Atau sesuaikan logika untuk 1 sesi

    # --- 2. Tren (7 sesi laporan terakhir) ---
    sesi_terakhir_untuk_tren = semua_laporan_selesai[-7:]
    tren_akurasi_data = { "labels": [], "data": [] }
    tren_durasi_data = { "labels": [], "data": [] }

    for laporan in sesi_terakhir_untuk_tren:
        label_sesi = laporan.tanggal_laporan.strftime('%d %b') if laporan.tanggal_laporan else "N/A"
        
        # Akurasi sesi
        hasil_detail_sesi = LaporanGerakanHasil.query.filter_by(laporan_rehabilitasi_id=laporan.id).all()
        total_gerakan_dilakukan_sesi = sum((h.jumlah_sempurna or 0) + (h.jumlah_tidak_sempurna or 0) + (h.jumlah_tidak_terdeteksi or 0) for h in hasil_detail_sesi)
        total_sempurna_sesi = sum(h.jumlah_sempurna or 0 for h in hasil_detail_sesi)
        akurasi_sesi_tren = (total_sempurna_sesi / total_gerakan_dilakukan_sesi) * 100 if total_gerakan_dilakukan_sesi > 0 else 0
        
        tren_akurasi_data["labels"].append(label_sesi)
        tren_akurasi_data["data"].append(round(akurasi_sesi_tren))

        # Durasi sesi (dalam menit)
        durasi_menit_sesi = (laporan.total_waktu_rehabilitasi_detik or 0) / 60.0
        tren_durasi_data["labels"].append(label_sesi) # Label bisa sama, atau unik per sesi
        tren_durasi_data["data"].append(round(durasi_menit_sesi))

    # --- 3. Distribusi Hasil Gerakan (Total dari semua laporan selesai) ---
    total_sempurna_all_sessions = 0
    total_tidak_sempurna_all_sessions = 0
    total_tidak_terdeteksi_all_sessions = 0
    
    for laporan in semua_laporan_selesai:
        for detail_hasil in laporan.detail_hasil_gerakan:
            total_sempurna_all_sessions += detail_hasil.jumlah_sempurna or 0
            total_tidak_sempurna_all_sessions += detail_hasil.jumlah_tidak_sempurna or 0
            total_tidak_terdeteksi_all_sessions += detail_hasil.jumlah_tidak_terdeteksi or 0

    # --- 4. Info Profil Pasien ---
    profil_pasien = PatientProfile.query.filter_by(user_id=pasien_id).first()

    # --- 5. Catatan Terbaru (contoh: 5 catatan terakhir dari program & laporan) ---
    # Ini bisa lebih kompleks, misal catatan dari terapis atau pasien sendiri
    # Untuk contoh, ambil catatan dari program dan laporan pasien
    catatan_terbaru = []
    program_terakhir_dengan_catatan = ProgramRehabilitasi.query\
        .filter(ProgramRehabilitasi.pasien_id == pasien_id, ProgramRehabilitasi.catatan_terapis != None, ProgramRehabilitasi.catatan_terapis != "")\
        .order_by(ProgramRehabilitasi.updated_at.desc()).limit(3).all()
    for prog in program_terakhir_dengan_catatan:
        catatan_terbaru.append({
            "tanggal": prog.updated_at.strftime('%Y-%m-%d'),
            "catatan": prog.catatan_terapis,
            "sumber": f"Terapis ({prog.terapis.nama_lengkap if prog.terapis else 'N/A'}) - Program: {prog.nama_program}"
        })
    
    laporan_terakhir_dengan_catatan = LaporanRehabilitasi.query\
        .filter(LaporanRehabilitasi.pasien_id == pasien_id, LaporanRehabilitasi.catatan_pasien_laporan != None, LaporanRehabilitasi.catatan_pasien_laporan != "")\
        .order_by(LaporanRehabilitasi.created_at.desc()).limit(3).all()
    for lap in laporan_terakhir_dengan_catatan:
        catatan_terbaru.append({
            "tanggal": lap.created_at.strftime('%Y-%m-%d'),
            "catatan": lap.catatan_pasien_laporan,
            "sumber": f"Pasien - Laporan Program: {lap.program_asli.nama_program if lap.program_asli else 'N/A'}"
        })
    
    # Urutkan catatan berdasarkan tanggal terbaru
    catatan_terbaru.sort(key=lambda x: x['tanggal'], reverse=True)
    catatan_terbaru = catatan_terbaru[:5] # Ambil 5 teratas

    # --- 6. Riwayat Aktivitas Monitoring (Ini adalah daftar program yang telah selesai) ---
    # UI mu sepertinya menampilkan riwayat program yang sudah selesai.
    # Ini bisa diambil dari `semua_laporan_selesai` dan mengambil info program aslinya.
    riwayat_aktivitas_monitoring = []
    for laporan in reversed(semua_laporan_selesai): # Urutan terbaru dulu
        if laporan.program_asli:
            riwayat_aktivitas_monitoring.append({
                "tanggal_program": laporan.program_asli.tanggal_program.strftime('%Y-%m-%d') if laporan.program_asli.tanggal_program else "N/A",
                "nama_program": laporan.program_asli.nama_program,
                "status_program": laporan.program_asli.status.value, # Selesai
                "laporan_id": laporan.id, # Untuk link ke detail laporan
                 # Tingkat kesulitan dan keterangan perlu model/logika tambahan jika ingin ditampilkan di sini
                "tingkat_kesulitan_dirasakan": "N/A", # Perlu field baru jika ini input dari pasien saat laporan
                "keterangan_sesi": laporan.catatan_pasien_laporan or "-"
            })


    response_data = {
        "pasien_info": {
            "nama_lengkap": pasien.nama_lengkap,
            "id_pasien_string": f"PAS{pasien.id:03}", # Contoh format ID Pasien
            "user_id": pasien.id, # ID numerik asli
            "jenis_kelamin": profil_pasien.jenis_kelamin if profil_pasien else "N/A",
            "tanggal_lahir": profil_pasien.tanggal_lahir.strftime('%d-%m-%Y') if profil_pasien and profil_pasien.tanggal_lahir else "N/A",
            "diagnosis": profil_pasien.diagnosis if profil_pasien else "N/A",
            "catatan_tambahan_pasien": profil_pasien.catatan_tambahan if profil_pasien else "N/A"
        },
        "summary_kpi": {
            "total_sesi_selesai": total_sesi_selesai,
            "rata_rata_akurasi_persen": round(rata_rata_akurasi_keseluruhan),
            "rata_rata_durasi_string": format_durasi_ringkas(rata_rata_durasi_detik),
            "rata_rata_durasi_detik": round(rata_rata_durasi_detik),
            "frekuensi_latihan_per_minggu": round(frekuensi_latihan, 1)
        },
        "trends_chart": {
            "akurasi_7_sesi_terakhir": tren_akurasi_data,
            "durasi_7_sesi_terakhir": tren_durasi_data # Data dalam menit
        },
        "distribusi_hasil_gerakan_total": { # Untuk pie/doughnut chart
            "labels": ["Sempurna", "Tidak Sempurna", "Tidak Terdeteksi"],
            "data": [total_sempurna_all_sessions, total_tidak_sempurna_all_sessions, total_tidak_terdeteksi_all_sessions]
        },
        "catatan_observasi_terbaru": catatan_terbaru,
        "riwayat_aktivitas_monitoring": riwayat_aktivitas_monitoring # Daftar program yang telah selesai
    }

    return jsonify(response_data), 200

