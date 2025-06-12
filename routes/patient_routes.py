# routes/patient_routes.py
# TERBARU: Logika update profil pasien agar memungkinkan field disetel ke null/kosong.
# Menambahkan endpoint untuk melihat Pola Makan (Diet Plan) oleh Pasien.
# Menambahkan endpoint baru untuk melihat program rehabilitasi dalam tampilan kalender.

from flask import Blueprint, request, jsonify, current_app
from models import AppUser, PatientProfile, PolaMakan, ProgramRehabilitasi, ProgramStatus, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import func
from utils.azure_helpers import upload_file_to_blob, delete_blob


patient_bp = Blueprint('patient_bp', __name__)

@patient_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    patient_profile = PatientProfile.query.filter_by(user_id=current_user_identity['id']).first_or_404("Profil pasien tidak ditemukan.")
    
    return jsonify(patient_profile.serialize_full())

@patient_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    user_id = current_user_identity['id']
    user = AppUser.query.get(user_id)
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    if not user or not patient_profile:
        return jsonify({"msg": "AppUser atau profil pasien tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    try:
        # Perbarui field-field dari AppUser
        # Jika 'nama_lengkap' ada dalam data, gunakan nilainya (termasuk null/kosong)
        if 'nama_lengkap' in data:
            user.nama_lengkap = data['nama_lengkap']
        
        # Perbarui username dengan validasi keunikan
        if 'username' in data:
            new_username = data['username']
            if new_username is not None and new_username != user.username: # Juga cek None
                if AppUser.query.filter_by(username=new_username).first():
                    return jsonify({"msg": "Username sudah terdaftar"}), 409
            user.username = new_username
        
        # Perbarui email dengan validasi keunikan
        if 'email' in data:
            new_email = data['email']
            if new_email is not None and new_email != user.email: # Juga cek None
                if AppUser.query.filter_by(email=new_email).first():
                    return jsonify({"msg": "Email sudah terdaftar"}), 409
            user.email = new_email
        
        # Perbarui field-field dari PatientProfile
        if 'jenis_kelamin' in data:
            patient_profile.jenis_kelamin = data['jenis_kelamin']
        
        if 'tanggal_lahir' in data:
            # Jika tanggal_lahir dikirim sebagai null atau string kosong, set ke None
            if data['tanggal_lahir']:
                try:
                    patient_profile.tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({"msg": "Format tanggal_lahir tidak valid (YYYY-MM-DD)"}), 400
            else:
                patient_profile.tanggal_lahir = None # Set to None if explicitly null/empty
        
        if 'tempat_lahir' in data:
            patient_profile.tempat_lahir = data['tempat_lahir']
        
        # Perbarui nomor_telepon dengan validasi keunikan
        if 'nomor_telepon' in data:
            new_nomor_telepon = data['nomor_telepon']
            if new_nomor_telepon is not None and new_nomor_telepon != patient_profile.nomor_telepon: # Juga cek None
                if PatientProfile.query.filter_by(nomor_telepon=new_nomor_telepon).first():
                    return jsonify({"msg": "Nomor telepon sudah terdaftar"}), 409
            patient_profile.nomor_telepon = new_nomor_telepon

        # Untuk field teks lainnya, gunakan pola 'if field_name in data'
        if 'alamat' in data:
            patient_profile.alamat = data['alamat']
        if 'nama_pendamping' in data:
            patient_profile.nama_pendamping = data['nama_pendamping']
        if 'diagnosis' in data:
            patient_profile.diagnosis = data['diagnosis']
        if 'catatan_tambahan' in data:
            patient_profile.catatan_tambahan = data['catatan_tambahan']
        if 'tinggi_badan' in data:
            patient_profile.tinggi_badan = data['tinggi_badan']
        if 'berat_badan' in data:
            patient_profile.berat_badan = data['berat_badan']
        if 'golongan_darah' in data:
            patient_profile.golongan_darah = data['golongan_darah']
        if 'riwayat_medis' in data:
            patient_profile.riwayat_medis = data['riwayat_medis']
        if 'riwayat_alergi' in data:
            patient_profile.riwayat_alergi = data['riwayat_alergi']

        db.session.commit()
        return jsonify({"msg": "Profil berhasil diperbarui", "profile": patient_profile.serialize_full()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profil gagal untuk user {user_id}: {str(e)}")
        return jsonify({"msg": "Update profil gagal", "error": str(e)}), 500


@patient_bp.route('/profile/picture', methods=['POST', 'PUT'])
@jwt_required()
def upload_profile_picture():
    """Endpoint untuk upload/update foto profil pasien."""
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    user_id = current_user_identity.get('id')
    profile = PatientProfile.query.filter_by(user_id=user_id).first_or_404("Profil tidak ditemukan")

    if 'foto_profil' not in request.files:
        return jsonify({"msg": "File 'foto_profil' tidak ditemukan dalam request"}), 400
    
    file = request.files['foto_profil']
    
    try:
        new_blob_name, err = upload_file_to_blob(file, 'profil/foto')
        if err:
            raise Exception(err)

        old_blob_name = profile.filename_foto_profil
        if old_blob_name:
            delete_blob(old_blob_name)

        profile.filename_foto_profil = new_blob_name
        db.session.commit()

        return jsonify({
            "msg": "Foto profil berhasil diupdate",
            "url_foto_profil": profile.serialize_full().get('url_foto_profil')
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal upload foto profil untuk user {user_id}: {str(e)}")
        return jsonify({"msg": "Gagal mengupdate foto profil", "error": str(e)}), 500


# NEW ENDPOINT: Get Patient's Diet Plan for a specific date
@patient_bp.route('/diet-plan/<string:tanggal_str>', methods=['GET'])
@jwt_required()
def get_patient_diet_plan(tanggal_str):
    """
    Endpoint untuk pasien melihat rencana pola makan mereka untuk tanggal tertentu.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')

    try:
        tanggal_makan = datetime.strptime(tanggal_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Format tanggal tidak valid (YYYY-MM-DD)"}), 400

    plan = PolaMakan.query.filter_by(pasien_id=pasien_id, tanggal_makan=tanggal_makan).first()

    if not plan:
        return jsonify({"msg": "Tidak ada rencana pola makan untuk tanggal ini."}), 404
    
    return jsonify(plan.serialize()), 200


# NEW ENDPOINT: Get Patient's Rehabilitation Programs for Calendar View
@patient_bp.route('/calendar-programs', methods=['GET'])
@jwt_required()
def get_patient_calendar_programs():
    """
    Endpoint untuk pasien mendapatkan daftar program rehabilitasi mereka
    untuk tampilan kalender, dengan filter berdasarkan rentang tanggal (opsional).
    Query params: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = ProgramRehabilitasi.query.filter_by(pasien_id=pasien_id)

    # Filter berdasarkan rentang tanggal jika disediakan
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(ProgramRehabilitasi.tanggal_program >= start_date)
        except ValueError:
            return jsonify({"msg": "Format start_date tidak valid (YYYY-MM-DD)"}), 400
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(ProgramRehabilitasi.tanggal_program <= end_date)
        except ValueError:
            return jsonify({"msg": "Format end_date tidak valid (YYYY-MM-DD)"}), 400

    # Urutkan berdasarkan tanggal program
    programs = query.order_by(ProgramRehabilitasi.tanggal_program.asc(), ProgramRehabilitasi.created_at.asc()).all()

    serialized_programs = []
    for p in programs:
        # Untuk kalender, kita mungkin hanya butuh informasi dasar
        serialized_programs.append({
            "id": p.id,
            "nama_program": p.nama_program,
            "tanggal_program": p.tanggal_program.isoformat() if p.tanggal_program else None,
            "status": p.status.value,
            "catatan_terapis": p.catatan_terapis,
            "terapis_nama": p.terapis.nama_lengkap if p.terapis else "N/A"
        })
    
    return jsonify({"programs": serialized_programs}), 200

