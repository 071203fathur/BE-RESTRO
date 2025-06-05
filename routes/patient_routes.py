# BE-RESTRO/routes/patient_routes.py

from flask import Blueprint, request, jsonify
from models import User, PatientProfile, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

patient_bp = Blueprint('patient_bp', __name__)

def is_pasien():
    current_user_identity = get_jwt_identity()
    return current_user_identity.get('role') == 'pasien'

@patient_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien': # Verifikasi role dari token
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa melihat profil ini"}), 403

    current_user_id = current_user_identity['id']
    patient_profile = PatientProfile.query.filter_by(user_id=current_user_id).first()

    if not patient_profile:
        return jsonify({"msg": "Profil pasien tidak ditemukan"}), 404
    return jsonify(patient_profile.serialize_full()), 200

@patient_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien': # Verifikasi role
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa memperbarui profil ini"}), 403

    current_user_id = current_user_identity['id']
    patient_profile = PatientProfile.query.filter_by(user_id=current_user_id).first()

    if not patient_profile:
        return jsonify({"msg": "Profil pasien tidak ditemukan"}), 404

    data = request.get_json()
    if not data: return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    user = patient_profile.user # Akses User dari profil
    if 'nama_lengkap' in data: user.nama_lengkap = data['nama_lengkap']
    if 'username' in data: # Tambahkan validasi unique jika username boleh diubah
        existing_user = User.query.filter(User.username == data['username'], User.id != user.id).first()
        if existing_user: return jsonify({"msg": "Username tersebut sudah digunakan"}), 409
        user.username = data['username']
    if 'email' in data: # Tambahkan validasi unique jika email boleh diubah
        existing_user = User.query.filter(User.email == data['email'], User.id != user.id).first()
        if existing_user: return jsonify({"msg": "Email tersebut sudah digunakan"}), 409
        user.email = data['email']


    patient_profile.jenis_kelamin = data.get('jenis_kelamin', patient_profile.jenis_kelamin)
    if data.get('tanggal_lahir'):
        try:
            patient_profile.tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Format tanggal_lahir salah (YYYY-MM-DD)"}), 400
    
    patient_profile.tempat_lahir = data.get('tempat_lahir', patient_profile.tempat_lahir)
    patient_profile.nomor_telepon = data.get('nomor_telepon', patient_profile.nomor_telepon)
    patient_profile.alamat = data.get('alamat', patient_profile.alamat)
    patient_profile.nama_pendamping = data.get('nama_pendamping', patient_profile.nama_pendamping)
    patient_profile.tinggi_badan = data.get('tinggi_badan', patient_profile.tinggi_badan)
    patient_profile.berat_badan = data.get('berat_badan', patient_profile.berat_badan)
    patient_profile.golongan_darah = data.get('golongan_darah', patient_profile.golongan_darah)
    patient_profile.riwayat_medis = data.get('riwayat_medis', patient_profile.riwayat_medis)
    patient_profile.riwayat_alergi = data.get('riwayat_alergi', patient_profile.riwayat_alergi)
    
    try:
        db.session.commit()
        return jsonify({"msg": "Profil pasien berhasil diperbarui", "profile": patient_profile.serialize_full()}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error update profil: {str(e)}")
        return jsonify({"msg": "Update profil pasien gagal", "error": "Kesalahan internal server"}), 500