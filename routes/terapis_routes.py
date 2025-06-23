# routes/terapis_routes.py
# PERUBAHAN: Menambahkan endpoint baru untuk mendapatkan daftar terapis dengan ID (untuk fitur chat/kontak).

from flask import Blueprint, jsonify, request
from models import db, AppUser, PatientProfile, ProgramRehabilitasi, ProgramStatus, PolaMakan
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, distinct
from datetime import date, timedelta, datetime
from calendar import monthrange
from collections import defaultdict

terapis_bp = Blueprint('terapis_bp', __name__)

@terapis_bp.route('/my-patients-details', methods=['GET'])
@jwt_required()
def get_my_patients_details():
    """
    Endpoint untuk terapis mendapatkan daftar pasien yang pernah mereka tangani,
    termasuk URL foto profil pasien.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    terapis_id = current_user_identity.get('id')

    assigned_patients = db.session.query(AppUser, PatientProfile).\
        join(ProgramRehabilitasi, AppUser.id == ProgramRehabilitasi.pasien_id).\
        outerjoin(PatientProfile, AppUser.id == PatientProfile.user_id).\
        filter(ProgramRehabilitasi.terapis_id == terapis_id).\
        distinct(AppUser.id).all()
    
    patients_list = []
    for patient_user, patient_profile in assigned_patients:
        if patient_profile:
            profile_data = patient_profile.serialize_full()
            patients_list.append({
                "id": profile_data.get('user_id'),
                "nama": profile_data.get('nama_lengkap'),
                "email": profile_data.get('email'),
                "foto_url": profile_data.get('url_foto_profil'),
                "diagnosis": profile_data.get('diagnosis', "Belum ada diagnosis")
            })
        else:
            patients_list.append({
                "id": patient_user.id,
                "nama": patient_user.nama_lengkap,
                "email": patient_user.email,
                "foto_url": None,
                "diagnosis": "Belum ada diagnosis"
            })

    return jsonify({"patients": patients_list}), 200


@terapis_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def get_terapis_dashboard_summary():
    """
    Endpoint untuk mendapatkan data ringkasan KPI dan data grafik untuk dashboard terapis.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    terapis_id = current_user_identity.get('id')
    today = date.today()

    total_pasien_ditangani_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id).scalar() or 0

    pasien_rehab_hari_ini_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id,
                ProgramRehabilitasi.tanggal_program == today,
                ProgramRehabilitasi.status.in_([ProgramStatus.BELUM_DIMULAI, ProgramStatus.BERJALAN]))\
        .scalar() or 0

    pasien_selesai_rehab_hari_ini_count = db.session.query(func.count(distinct(ProgramRehabilitasi.pasien_id)))\
        .filter(ProgramRehabilitasi.terapis_id == terapis_id,
                ProgramRehabilitasi.status == ProgramStatus.SELESAI,
                db.func.date(ProgramRehabilitasi.updated_at) == today)\
        .scalar() or 0

    program_terbaru_query = ProgramRehabilitasi.query.filter_by(terapis_id=terapis_id)\
        .order_by(ProgramRehabilitasi.created_at.desc())\
        .limit(2).all()
    
    program_terbaru_serialized = []
    for p in program_terbaru_query:
        program_data = p.serialize_full()
        program_terbaru_serialized.append({
            "id": program_data.get('id'),
            "program_name": program_data.get('nama_program'),
            "patient_id": program_data.get('pasien', {}).get('id'),
            "patient_name": program_data.get('pasien', {}).get('nama_lengkap'),
            "execution_date": program_data.get('tanggal_program'),
            "status": program_data.get('status'),
            "catatan_terapis": program_data.get('catatan_terapis'),
            "movements_details": program_data.get('list_gerakan_direncanakan')
        })

    end_date = today
    start_date = today - timedelta(days=29)

    daily_new_patients = defaultdict(int)

    subquery_first_program_date = db.session.query(
        ProgramRehabilitasi.pasien_id,
        func.min(ProgramRehabilitasi.created_at).label('first_assigned_date')
    ).filter(
        ProgramRehabilitasi.terapis_id == terapis_id,
        ProgramRehabilitasi.created_at >= start_date,
        ProgramRehabilitasi.created_at <= end_date + timedelta(days=1)
    ).group_by(ProgramRehabilitasi.pasien_id).subquery()

    patients_first_assigned_in_range = db.session.query(
        db.func.date(subquery_first_program_date.c.first_assigned_date),
        func.count(subquery_first_program_date.c.pasien_id)
    ).filter(
        db.func.date(subquery_first_program_date.c.first_assigned_date) >= start_date,
        db.func.date(subquery_first_program_date.c.first_assigned_date) <= end_date
    ).group_by(db.func.date(subquery_first_program_date.c.first_assigned_date))\
    .order_by(db.func.date(subquery_first_program_date.c.first_assigned_date)).all()

    for assign_date, count in patients_first_assigned_in_range:
        daily_new_patients[assign_date] = count

    chart_labels = []
    chart_data = []
    current_date = start_date
    while current_date <= end_date:
        chart_labels.append(current_date.strftime('%d %b'))
        chart_data.append(daily_new_patients[current_date])
        current_date += timedelta(days=1)

    dashboard_data = {
        "kpi": {
            "total_pasien_ditangani": total_pasien_ditangani_count,
            "pasien_rehabilitasi_hari_ini": pasien_rehab_hari_ini_count,
            "pasien_selesai_rehabilitasi_hari_ini": pasien_selesai_rehab_hari_ini_count
        },
        "program_terbaru_terapis": program_terbaru_serialized,
        "chart_data_patients_per_day": {
            "labels": chart_labels,
            "data": chart_data
        }
    }

    return jsonify(dashboard_data), 200

# NEW ENDPOINTS FOR DIET PLAN MANAGEMENT (by Terapis)
@terapis_bp.route('/diet-plan', methods=['POST'])
@jwt_required()
def create_diet_plan():
    """
    Endpoint untuk terapis membuat rencana pola makan baru untuk pasien.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    terapis_id = current_user_identity.get('id')
    data = request.get_json()

    pasien_id = data.get('pasien_id')
    tanggal_makan_str = data.get('tanggal_makan')
    menu_pagi = data.get('menu_pagi')
    menu_siang = data.get('menu_siang')
    menu_malam = data.get('menu_malam')
    cemilan = data.get('cemilan')

    if not all([pasien_id, tanggal_makan_str]):
        return jsonify({"msg": "ID Pasien dan Tanggal Makan wajib diisi"}), 400
    
    pasien = AppUser.query.filter_by(id=pasien_id, role='pasien').first_or_404("Pasien tidak ditemukan.")

    try:
        tanggal_makan = datetime.strptime(tanggal_makan_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Format tanggal_makan tidak valid (YYYY-MM-DD)"}), 400

    # Cek apakah sudah ada pola makan untuk pasien dan tanggal yang sama
    existing_plan = PolaMakan.query.filter_by(pasien_id=pasien_id, tanggal_makan=tanggal_makan).first()
    if existing_plan:
        return jsonify({"msg": "Pola makan untuk pasien dan tanggal ini sudah ada. Gunakan PUT untuk update."}), 409

    new_plan = PolaMakan(
        pasien_id=pasien_id,
        terapis_id=terapis_id,
        tanggal_makan=tanggal_makan,
        menu_pagi=menu_pagi,
        menu_siang=menu_siang,
        menu_malam=menu_malam,
        cemilan=cemilan
    )

    try:
        db.session.add(new_plan)
        db.session.commit()
        return jsonify({"msg": "Pola makan berhasil dibuat", "pola_makan": new_plan.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal membuat pola makan", "error": str(e)}), 500

@terapis_bp.route('/diet-plan/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_diet_plan(plan_id):
    """
    Endpoint untuk terapis memperbarui rencana pola makan pasien.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    terapis_id = current_user_identity.get('id')
    plan = PolaMakan.query.filter_by(id=plan_id, terapis_id=terapis_id).first_or_404("Pola makan tidak ditemukan atau Anda tidak berhak mengeditnya.")

    data = request.get_json()
    
    plan.menu_pagi = data.get('menu_pagi', plan.menu_pagi)
    plan.menu_siang = data.get('menu_siang', plan.menu_siang)
    plan.menu_malam = data.get('menu_malam', plan.menu_malam)
    plan.cemilan = data.get('cemilan', plan.cemilan)

    try:
        db.session.commit()
        return jsonify({"msg": "Pola makan berhasil diperbarui", "pola_makan": plan.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal memperbarui pola makan", "error": str(e)}), 500

@terapis_bp.route('/diet-plan/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_diet_plan(plan_id):
    """
    Endpoint untuk terapis menghapus rencana pola makan pasien.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    terapis_id = current_user_identity.get('id')
    plan = PolaMakan.query.filter_by(id=plan_id, terapis_id=terapis_id).first_or_404("Pola makan tidak ditemukan atau Anda tidak berhak menghapusnya.")

    try:
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"msg": "Pola makan berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal menghapus pola makan", "error": str(e)}), 500

@terapis_bp.route('/diet-plan/patient/<int:pasien_id>/<string:tanggal_str>', methods=['GET'])
@jwt_required()
def get_diet_plan_for_patient_on_date(pasien_id, tanggal_str):
    """
    Endpoint untuk terapis mendapatkan pola makan spesifik untuk pasien dan tanggal tertentu.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    try:
        # Menghilangkan spasi di awal/akhir string tanggal
        tanggal_makan = datetime.strptime(tanggal_str.strip(), '%Y-%m-%d').date()
    except ValueError as e:
        # Mencetak error detail untuk debugging
        print(f"DEBUG: ValueError in date parsing for get_diet_plan_for_patient_on_date: {e}. Received tanggal_str: '{tanggal_str}'")
        return jsonify({"msg": "Format tanggal tidak valid (YYYY-MM-DD)"}), 400

    plan = PolaMakan.query.filter_by(pasien_id=pasien_id, tanggal_makan=tanggal_makan).first()

    if not plan:
        return jsonify({"msg": "Pola makan tidak ditemukan untuk pasien ini pada tanggal tersebut."}), 404
    
    return jsonify(plan.serialize()), 200

@terapis_bp.route('/diet-plan/patient/<int:pasien_id>/all', methods=['GET'])
@jwt_required()
def get_all_diet_plans_for_patient(pasien_id):
    """
    Endpoint baru untuk terapis mendapatkan semua pola makan untuk pasien tertentu.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    plans = PolaMakan.query.filter_by(pasien_id=pasien_id).order_by(PolaMakan.tanggal_makan.desc()).all()

    return jsonify({"pola_makan": [p.serialize() for p in plans]}), 200

@terapis_bp.route('/list-all-terapis', methods=['GET'])
@jwt_required()
def list_all_terapis():
    """
    Endpoint untuk mendapatkan daftar semua terapis dengan ID dan nama lengkap mereka.
    Dapat diakses oleh pasien atau terapis. Berguna untuk memulai chat atau menampilkan daftar kontak.
    """
    current_user_identity = get_jwt_identity()
    user_role = current_user_identity.get('role')

    # Hanya izinkan pasien dan terapis untuk mengakses
    if user_role not in ['pasien', 'terapis']:
        return jsonify({"msg": "Akses ditolak: Hanya pasien dan terapis yang dapat mengakses daftar terapis."}), 403

    terapis_list = AppUser.query.filter_by(role='terapis').all()

    result = []
    for terapis in terapis_list:
        result.append({
            "id": terapis.id,
            "username": terapis.username,
            "nama_lengkap": terapis.nama_lengkap,
            "email": terapis.email
        })
    return jsonify({"terapis_list": result}), 200
