# routes/program_routes.py
# TERBARU: Menampilkan foto pasien, diagnosis, DAN TOTAL POIN di endpoint /pasien-list
# Menambahkan endpoint baru /program/patient-info/<int:pasien_id>
# untuk mendapatkan info pasien dasar, sekarang termasuk total_points.

from flask import Blueprint, request, jsonify
from models import db, AppUser, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, ProgramStatus, PatientProfile
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime

program_bp = Blueprint('program_bp', __name__)

@program_bp.route('/pasien-list', methods=['GET'])
@jwt_required()
def get_pasien_list_for_terapis():
    """
    Endpoint untuk terapis mendapatkan daftar pasien (untuk dropdown program),
    sekarang termasuk foto profil, diagnosis pasien, dan total poin.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    # Query untuk mengambil semua AppUser dengan role 'pasien'
    # dan melakukan outerjoin dengan PatientProfile untuk mendapatkan data tambahan.
    pasien_records = db.session.query(AppUser, PatientProfile).\
        filter(AppUser.role == 'pasien').\
        outerjoin(PatientProfile, AppUser.id == PatientProfile.user_id).\
        order_by(AppUser.nama_lengkap.asc()).all()
    
    pasien_list = []
    for user, profile in pasien_records:
        patient_data = {
            "id": user.id,
            "username": user.username,
            "nama_lengkap": user.nama_lengkap,
            "email": user.email,
            "role": user.role,
            "total_points": user.total_points, # <--- TAMBAH INI
        }
        
        # Tambahkan data dari PatientProfile jika ada
        if profile:
            patient_data["foto_url"] = profile.serialize_full().get('url_foto_profil')
            patient_data["diagnosis"] = profile.diagnosis
        else:
            patient_data["foto_url"] = None
            patient_data["diagnosis"] = "Belum ada diagnosis" # Default jika tidak ada profil

        pasien_list.append(patient_data)

    return jsonify(pasien_list), 200

@program_bp.route('/patient-info/<int:pasien_id>', methods=['GET'])
@jwt_required()
def get_patient_info_for_program_context(pasien_id):
    """
    Endpoint untuk mendapatkan informasi dasar pasien (termasuk foto, diagnosis, dan total poin)
    dalam konteks modul program. Dapat diakses oleh terapis.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang dapat mengakses info pasien."}), 403
    
    # Gabungkan AppUser dan PatientProfile
    user_record = db.session.query(AppUser, PatientProfile).\
        filter(AppUser.id == pasien_id, AppUser.role == 'pasien').\
        outerjoin(PatientProfile, AppUser.id == PatientProfile.user_id).\
        first()

    if not user_record:
        return jsonify({"msg": f"Pasien dengan ID {pasien_id} tidak ditemukan."}), 404

    user, profile = user_record
    
    patient_info = {
        "id": user.id,
        "username": user.username,
        "nama_lengkap": user.nama_lengkap,
        "email": user.email,
        "role": user.role,
        "total_points": user.total_points, # <--- TAMBAH INI
    }

    if profile:
        patient_info["foto_url"] = profile.serialize_full().get('url_foto_profil')
        patient_info["diagnosis"] = profile.diagnosis
        patient_info["jenis_kelamin"] = profile.jenis_kelamin
        patient_info["tanggal_lahir"] = profile.tanggal_lahir.isoformat() if profile.tanggal_lahir else None
        # Anda bisa menambahkan field lain yang relevan dari PatientProfile di sini
    else:
        patient_info["foto_url"] = None
        patient_info["diagnosis"] = "Belum ada diagnosis"
        patient_info["jenis_kelamin"] = None
        patient_info["tanggal_lahir"] = None

    return jsonify(patient_info), 200


@program_bp.route('/', methods=['POST'])
@jwt_required()
def create_and_assign_program():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    data = request.get_json()
    nama_program = data.get('nama_program')
    pasien_id = data.get('pasien_id')
    list_gerakan_input = data.get('list_gerakan_direncanakan')
    tanggal_program_str = data.get('tanggal_program')
    catatan_terapis = data.get('catatan_terapis')
    status_program_str = data.get('status', ProgramStatus.BELUM_DIMULAI.value)

    if not all([nama_program, pasien_id, list_gerakan_input]):
        return jsonify({"msg": "Nama program, ID pasien, dan daftar gerakan wajib diisi"}), 400
    
    pasien = AppUser.query.filter_by(id=pasien_id, role='pasien').first_or_404("Pasien tidak ditemukan.")

    try:
        tanggal_program = datetime.strptime(tanggal_program_str, '%Y-%m-%d').date() if tanggal_program_str else date.today()
        status_program = ProgramStatus(status_program_str)
    except (ValueError, TypeError):
        return jsonify({"msg": "Format tanggal atau status tidak valid"}), 400

    new_program = ProgramRehabilitasi(
        nama_program=nama_program,
        tanggal_program=tanggal_program,
        catatan_terapis=catatan_terapis,
        status=status_program,
        terapis_id=current_user_identity.get('id'),
        pasien_id=pasien_id
    )
    
    try:
        db.session.add(new_program)
        db.session.flush()

        for idx, item_gerakan in enumerate(list_gerakan_input):
            gerakan_id = item_gerakan.get('gerakan_id')
            jumlah_repetisi = item_gerakan.get('jumlah_repetisi_direncanakan')
            urutan = item_gerakan.get('urutan_dalam_program', idx + 1)

            if not gerakan_id or not isinstance(jumlah_repetisi, int) or jumlah_repetisi <= 0:
                raise ValueError(f"Data gerakan tidak valid pada item {idx+1}")
            
            if not Gerakan.query.get(gerakan_id):
                raise ValueError(f"Gerakan dengan ID {gerakan_id} tidak ditemukan")

            detail = ProgramGerakanDetail(
                program_id=new_program.id,
                gerakan_id=gerakan_id,
                jumlah_repetisi=jumlah_repetisi,
                urutan=urutan
            )
            db.session.add(detail)
        
        db.session.commit()
        return jsonify({"msg": "Program berhasil dibuat", "program": new_program.serialize_full()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal membuat program", "error": str(e)}), 500


@program_bp.route('/pasien/today', methods=['GET'])
@jwt_required()
def get_program_pasien_today():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    pasien_id = current_user_identity.get('id')
    today = date.today()

    program = ProgramRehabilitasi.query.filter(
        ProgramRehabilitasi.pasien_id == pasien_id,
        ProgramRehabilitasi.tanggal_program <= today,
        ProgramRehabilitasi.status.in_([ProgramStatus.BELUM_DIMULAI, ProgramStatus.BERJALAN])
    ).order_by(ProgramRehabilitasi.tanggal_program.asc()).first()
    
    if not program:
        return jsonify({"msg": "Tidak ada program aktif yang dijadwalkan."}), 404
        
    return jsonify(program.serialize_full()), 200


@program_bp.route('/pasien/history', methods=['GET'])
@jwt_required()
def get_program_history_pasien():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated_programs = ProgramRehabilitasi.query.filter_by(pasien_id=pasien_id)\
        .order_by(ProgramRehabilitasi.tanggal_program.desc(), ProgramRehabilitasi.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    results = [p.serialize_full() for p in paginated_programs.items]

    return jsonify({
        "programs": results,
        "total_items": paginated_programs.total,
        "total_pages": paginated_programs.pages,
        "current_page": paginated_programs.page
    }), 200

# NEW ENDPOINT: Get programs assigned to a specific patient by therapist
@program_bp.route('/terapis/assigned-to-patient/<int:pasien_id>', methods=['GET'])
@jwt_required()
def get_assigned_programs_for_patient(pasien_id):
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    # Ensure the patient exists
    pasien = AppUser.query.filter_by(id=pasien_id, role='pasien').first_or_404("Pasien tidak ditemukan.")

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int) # Default higher for this view

    # Query for programs assigned to this patient by the current therapist
    paginated_programs = ProgramRehabilitasi.query.filter(
        ProgramRehabilitasi.pasien_id == pasien_id,
        ProgramRehabilitasi.terapis_id == current_user_identity.get('id')
    ).order_by(ProgramRehabilitasi.tanggal_program.desc(), ProgramRehabilitasi.created_at.desc())\
     .paginate(page=page, per_page=per_page, error_out=False)

    results = [p.serialize_full() for p in paginated_programs.items]

    return jsonify({
        "msg": f"Daftar program yang di-assign ke pasien {pasien.nama_lengkap} berhasil diambil",
        "programs": results,
        "total_items": paginated_programs.total,
        "total_pages": paginated_programs.pages,
        "current_page": paginated_programs.page
    }), 200

# Endpoint lainnya juga disesuaikan dengan cara yang sama
@program_bp.route('/<int:program_id>', methods=['GET'])
@jwt_required()
def get_program_detail(program_id):
    program = ProgramRehabilitasi.query.get_or_404(program_id)
    # Check authorization: either patient owner or assigned therapist
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') == 'pasien' and program.pasien_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403
    elif current_user_identity.get('role') == 'terapis' and program.terapis_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403

    return jsonify({"msg": "Detail program berhasil diambil", "program": program.serialize_full()}), 200


@program_bp.route('/<int:program_id>/update-status', methods=['PUT'])
@jwt_required()
def update_program_status(program_id):
    current_user_identity = get_jwt_identity()
    
    program = ProgramRehabilitasi.query.get_or_404(program_id)

    # Authorization check
    if current_user_identity.get('role') == 'pasien' and program.pasien_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403
    if current_user_identity.get('role') == 'terapis' and program.terapis_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403

    data = request.get_json()
    new_status_str = data.get('status')

    if not new_status_str:
        return jsonify({"msg": "Status baru harus disediakan"}), 400

    try:
        new_status = ProgramStatus(new_status_str)
    except ValueError:
        return jsonify({"msg": "Status tidak valid"}), 400

    # Only therapist or system can change to 'selesai' or 'dibatalkan'
    # Patient can only change from 'belum_dimulai' to 'berjalan'
    if current_user_identity.get('role') == 'pasien' and \
       (new_status == ProgramStatus.SELESAI or new_status == ProgramStatus.DIBATALKAN):
        return jsonify({"msg": "Pasien tidak diizinkan mengubah status menjadi selesai atau dibatalkan langsung."}), 403

    program.status = new_status
    db.session.commit()

    return jsonify({
        "msg": f"Status program berhasil diubah menjadi '{new_status.value}'",
        "program": program.serialize_simple()
    }), 200
