# BE-RESTRO/routes/terapis_routes.py

from flask import Blueprint, jsonify
from models import db, User, PatientProfile, ProgramRehabilitasi, ProgramStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, distinct
from datetime import date, timedelta, datetime

terapis_bp = Blueprint('terapis_bp', __name__)

@terapis_bp.route('/my-patients-details', methods=['GET'])
@jwt_required()
def get_my_patients_details():
    """
    Endpoint untuk terapis mendapatkan daftar pasien yang pernah mereka tangani.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    terapis_id = current_user_identity.get('id')

    # Query untuk mendapatkan objek User dari pasien yang pernah di-assign program oleh terapis ini
    assigned_patients = User.query.join(ProgramRehabilitasi, User.id == ProgramRehabilitasi.pasien_id)\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id)\
        .distinct().all()
    
    patients_list = []
    for patient_user in assigned_patients:
        # Kita perlu data dari User dan PatientProfile, jadi kita panggil serialize_full dari profilnya
        if patient_user.patient_profile:
            profile_data = patient_user.patient_profile.serialize_full()
            patients_list.append({
                "id": profile_data.get('user_id'),
                "nama": profile_data.get('nama_lengkap'),
                "email": profile_data.get('email'),
                "foto_url": profile_data.get('url_foto_profil'),
                "diagnosis": profile_data.get('diagnosis', "Belum ada diagnosis")
            })

    return jsonify({"patients": patients_list}), 200


@terapis_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def get_terapis_dashboard_summary():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    terapis_id = current_user_identity.get('id')

    # Query KPI (logika tetap sama seperti sebelumnya)
    total_pasien_ditangani_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id).scalar() or 0

    pasien_selesai_rehab_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id, ProgramRehabilitasi.status == ProgramStatus.SELESAI)\
        .scalar() or 0
    
    # Dua Program Kegiatan Terbaru
    program_terbaru_query = ProgramRehabilitasi.query.filter_by(terapis_id=terapis_id)\
        .order_by(ProgramRehabilitasi.created_at.desc())\
        .limit(2).all()
    
    # DIUBAH: Menghapus parameter config
    program_terbaru_serialized = [p.serialize_full() for p in program_terbaru_query]

    dashboard_data = {
        "kpi": {
            "total_pasien_ditangani_terapis": total_pasien_ditangani_count,
            "pasien_selesai_rehabilitasi_terapis": pasien_selesai_rehab_count
        },
        "program_terbaru_terapis": program_terbaru_serialized,
        # ... (statistik lainnya bisa ditambahkan kembali jika perlu) ...
    }

    return jsonify(dashboard_data), 200
