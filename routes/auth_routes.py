# BE-RESTRO/routes/auth_routes.py

from flask import Blueprint, request, jsonify
from models import AppUser, PatientProfile, db # Pastikan db dan model lain diimport
from app import bcrypt # Import bcrypt dari app.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta 

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/terapis/register', methods=['POST'])
def register_terapis():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    username = data.get('username')
    nama_lengkap = data.get('nama_lengkap')
    email = data.get('email')
    password = data.get('password')

    if not all([username, nama_lengkap, email, password]):
        return jsonify({"msg": "Semua field (username, nama_lengkap, email, password) harus diisi"}), 400

    # 2. Ganti User menjadi AppUser
    if AppUser.query.filter_by(username=data.get('username')).first():
        return jsonify({"msg": "Username sudah terdaftar"}), 409
    if AppUser.query.filter_by(email=data.get('email')).first():
        return jsonify({"msg": "Email sudah terdaftar"}), 409

    new_terapis = AppUser(
        username=username,
        nama_lengkap=nama_lengkap,
        email=email,
        role='terapis'
    )
    new_terapis.set_password(password)

    try:
        db.session.add(new_terapis)
        db.session.commit()
        return jsonify({"msg": "Registrasi terapis berhasil", "user": new_terapis.serialize_basic()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Registrasi terapis gagal", "error": str(e)}), 500

@auth_bp.route('/terapis/login', methods=['POST'])
def login_terapis():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400
    
    identifier = data.get('identifier') # Bisa username atau email
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"msg": "Identifier (username/email) dan password harus diisi"}), 400

    user = AppUser.query.filter(
        (AppUser.email == identifier) | (AppUser.username == identifier),
        AppUser.role == 'terapis'
    ).first()

    if user and user.check_password(password):
        expires = timedelta(days=1) # Token berlaku 1 hari
        access_token = create_access_token(
            identity={'id': user.id, 'username': user.username, 'role': user.role, 'nama_lengkap': user.nama_lengkap},
            expires_delta=expires
        )
        return jsonify(access_token=access_token, user=user.serialize_basic()), 200
    else:
        return jsonify({"msg": "Identifier atau password salah"}), 401


@auth_bp.route('/pasien/register', methods=['POST'])
def register_pasien():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    username = data.get('username')
    nama_lengkap = data.get('nama_lengkap')
    email = data.get('email')
    password = data.get('password')
    nomor_telepon = data.get('nomor_telepon') 

    if not all([username, nama_lengkap, email, password]):
        return jsonify({"msg": "Semua field (username, nama_lengkap, email, password) harus diisi"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username sudah terdaftar"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email sudah terdaftar"}), 409
    if nomor_telepon and PatientProfile.query.filter_by(nomor_telepon=nomor_telepon).first():
        return jsonify({"msg": "Nomor telepon sudah terdaftar"}), 409


    new_pasien_user = User(
        username=username,
        nama_lengkap=nama_lengkap,
        email=email,
        role='pasien'
    )
    new_pasien_user.set_password(password)

    new_patient_profile = PatientProfile(
        user=new_pasien_user, 
        nomor_telepon=nomor_telepon
    )
    
    try:
        db.session.add(new_pasien_user)
        db.session.add(new_patient_profile)
        db.session.commit()
        
        user_data = new_pasien_user.serialize_basic()
        
        return jsonify({
            "msg": "Registrasi pasien berhasil", 
            "user": user_data,
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error registrasi pasien: {str(e)}") # Logging untuk debug server
        return jsonify({"msg": "Registrasi pasien gagal", "error": "Terjadi kesalahan internal server"}), 500


@auth_bp.route('/pasien/login', methods=['POST'])
def login_pasien():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong"}), 400
        
    identifier = data.get('identifier') 
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"msg": "Identifier (username/email) dan password harus diisi"}), 400

    user = AppUser.query.filter(
        (AppUser.email == identifier) | (AppUser.username == identifier),
        AppUser.role == 'pasien'
    ).first()

    if user and user.check_password(password):
        expires = timedelta(days=1) 
        access_token = create_access_token(
            identity={'id': user.id, 'username': user.username, 'role': user.role, 'nama_lengkap': user.nama_lengkap},
            expires_delta=expires
        )
        return jsonify(access_token=access_token, user=user.serialize_basic()), 200
    else:
        return jsonify({"msg": "Identifier atau password salah"}), 401

@auth_bp.route('/logout', methods=['POST'])
@jwt_required() 
def logout():
    # Implementasi blocklist token akan lebih aman, tapi memerlukan setup tambahan (misal dengan Redis).
    # Untuk saat ini, client bertanggung jawab menghapus token.
    current_user_identity = get_jwt_identity()
    return jsonify(msg=f"User '{current_user_identity.get('username')}' logged out. Harap hapus token di sisi client."), 200

