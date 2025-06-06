# BE-RESTRO/routes/patient_routes.py

from flask import Blueprint, request, jsonify
from models import User, PatientProfile, db # Pastikan db diimport dari app atau models
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

patient_bp = Blueprint('patient_bp', __name__) # Nama blueprint diubah agar unik

@patient_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa melihat profil ini"}), 403

    current_user_id = current_user_identity['id']
    
    # Ambil user dan profil terkait
    user = User.query.get(current_user_id)
    if not user: # Seharusnya tidak terjadi jika token valid
        return jsonify({"msg": "User tidak ditemukan"}), 404

    patient_profile = PatientProfile.query.filter_by(user_id=current_user_id).first()

    if not patient_profile:
        # Jika profil belum ada, mungkin perlu dibuatkan secara otomatis atau beri pesan error
        # Untuk saat ini, kita anggap profil sudah dibuat saat registrasi
        return jsonify({"msg": "Profil pasien tidak ditemukan. Harap lengkapi profil Anda."}), 404
    
    return jsonify(patient_profile.serialize_full()), 200


@patient_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa memperbarui profil ini"}), 403

    current_user_id = current_user_identity['id']
    user = User.query.get(current_user_id)
    patient_profile = PatientProfile.query.filter_by(user_id=current_user_id).first()

    if not user or not patient_profile:
        return jsonify({"msg": "User atau profil pasien tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    # Update field User jika ada dan diizinkan
    if 'nama_lengkap' in data:
        user.nama_lengkap = data['nama_lengkap']
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"msg": "Username sudah digunakan"}), 409
        user.username = data['username']
    # Email biasanya tidak diubah dengan mudah, tapi jika perlu:
    # if 'email' in data and data['email'] != user.email:
    #     if User.query.filter_by(email=data['email']).first():
    #         return jsonify({"msg": "Email sudah digunakan"}), 409
    #     user.email = data['email']

    # Update field PatientProfile
    patient_profile.jenis_kelamin = data.get('jenis_kelamin', patient_profile.jenis_kelamin)
    
    if data.get('tanggal_lahir'):
        try:
            patient_profile.tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify({"msg": "Format tanggal_lahir salah. Gunakan YYYY-MM-DD"}), 400
    
    patient_profile.tempat_lahir = data.get('tempat_lahir', patient_profile.tempat_lahir)
    
    if 'nomor_telepon' in data and data['nomor_telepon'] != patient_profile.nomor_telepon:
        if PatientProfile.query.filter_by(nomor_telepon=data['nomor_telepon']).first():
             return jsonify({"msg": "Nomor telepon sudah digunakan"}), 409
        patient_profile.nomor_telepon = data['nomor_telepon']

    patient_profile.alamat = data.get('alamat', patient_profile.alamat)
    patient_profile.nama_pendamping = data.get('nama_pendamping', patient_profile.nama_pendamping)
    
    # Kolom baru dari permintaan monitoring
    patient_profile.diagnosis = data.get('diagnosis', patient_profile.diagnosis)
    patient_profile.catatan_tambahan = data.get('catatan_tambahan', patient_profile.catatan_tambahan)

    # Informasi Kesehatan
    patient_profile.tinggi_badan = data.get('tinggi_badan', patient_profile.tinggi_badan)
    patient_profile.berat_badan = data.get('berat_badan', patient_profile.berat_badan)
    patient_profile.golongan_darah = data.get('golongan_darah', patient_profile.golongan_darah)
    patient_profile.riwayat_medis = data.get('riwayat_medis', patient_profile.riwayat_medis)
    patient_profile.riwayat_alergi = data.get('riwayat_alergi', patient_profile.riwayat_alergi)
    
    patient_profile.updated_at = datetime.utcnow() # Update timestamp

    try:
        db.session.commit()
        return jsonify({"msg": "Profil pasien berhasil diperbarui", "profile": patient_profile.serialize_full()}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error update profil pasien: {str(e)}") # Logging untuk debug server
        return jsonify({"msg": "Update profil pasien gagal", "error": "Terjadi kesalahan internal server"}), 500
