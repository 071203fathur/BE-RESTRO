# BE-RESTRO/routes/patient_routes.py

from flask import Blueprint, request, jsonify, current_app
from models import AppUser, PatientProfile, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
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

    # Update data user dan profil (logika sama seperti sebelumnya)
    # ... (kode update nama_lengkap, username, dll tetap sama)

    try:
        # Kode untuk update field lainnya...
        user.nama_lengkap = data.get('nama_lengkap', user.nama_lengkap)
        # ... dan seterusnya untuk semua field teks
        patient_profile.jenis_kelamin = data.get('jenis_kelamin', patient_profile.jenis_kelamin)
        if data.get('tanggal_lahir'):
            patient_profile.tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()

        db.session.commit()
        return jsonify({"msg": "Profil berhasil diperbarui", "profile": patient_profile.serialize_full()}), 200
    except Exception as e:
        db.session.rollback()
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
        # Upload foto baru ke Azure
        new_blob_name, err = upload_file_to_blob(file, 'profil/foto')
        if err:
            raise Exception(err)

        # Hapus foto lama jika ada
        old_blob_name = profile.filename_foto_profil
        if old_blob_name:
            delete_blob(old_blob_name)

        # Simpan nama blob baru ke DB
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

