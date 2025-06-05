# BE-RESTRO/routes/auth_routes.py

from flask import Blueprint, request, jsonify
from models import User, PatientProfile, db
from app import bcrypt # Import bcrypt dari app.py utama
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

auth_bp = Blueprint('auth_bp', __name__)

# --- Registrasi Terapis ---
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

    if User.query.filter_by(username=username).first() or \
       User.query.filter_by(email=email).first():
        return jsonify({"msg": "Username atau email sudah terdaftar"}), 409

    new_terapis = User(username=username, nama_lengkap=nama_lengkap, email=email, role='terapis')
    new_terapis.set_password(password)

    try:
        db.session.add(new_terapis)
        db.session.commit()
        return jsonify({"msg": "Registrasi terapis berhasil", "user": new_terapis.serialize_basic()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Registrasi terapis gagal", "error": str(e)}), 500

# --- Login Terapis ---
@auth_bp.route('/terapis/login', methods=['POST'])
def login_terapis():
    data = request.get_json()
    if not data: return jsonify({"msg": "Request body tidak boleh kosong"}), 400
    
    identifier = data.get('identifier') # username atau email
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"msg": "Identifier dan password harus diisi"}), 400

    user = User.query.filter(
        ((User.email == identifier) | (User.username == identifier)),
        User.role == 'terapis'
    ).first()

    if user and user.check_password(password):
        expires = timedelta(days=1)
        access_token = create_access_token(
            identity={'id': user.id, 'username': user.username, 'role': user.role},
            expires_delta=expires
        )
        return jsonify(access_token=access_token, user=user.serialize_basic()), 200
    return jsonify({"msg": "Identifier atau password salah"}), 401

# --- Registrasi Pasien ---
@auth_bp.route('/pasien/register', methods=['POST'])
def register_pasien():
    data = request.get_json()
    if not data: return jsonify({"msg": "Request body tidak boleh kosong"}), 400

    username = data.get('username')
    nama_lengkap = data.get('nama_lengkap')
    email = data.get('email')
    password = data.get('password')
    nomor_telepon = data.get('nomor_telepon') 

    if not all([username, nama_lengkap, email, password]):
        return jsonify({"msg": "Field (username, nama_lengkap, email, password) wajib diisi"}), 400

    if User.query.filter_by(username=username).first() or \
       User.query.filter_by(email=email).first():
        return jsonify({"msg": "Username atau email sudah terdaftar"}), 409

    new_pasien_user = User(username=username, nama_lengkap=nama_lengkap, email=email, role='pasien')
    new_pasien_user.set_password(password)
    new_patient_profile = PatientProfile(user=new_pasien_user, nomor_telepon=nomor_telepon)
    
    try:
        db.session.add(new_pasien_user)
        db.session.add(new_patient_profile) # Tambahkan profile juga
        db.session.commit()
        return jsonify({
            "msg": "Registrasi pasien berhasil", 
            "user": new_pasien_user.serialize_basic(),
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error registrasi pasien: {str(e)}")
        return jsonify({"msg": "Registrasi pasien gagal", "error": "Kesalahan internal server"}), 500

# --- Login Pasien ---
@auth_bp.route('/pasien/login', methods=['POST'])
def login_pasien():
    data = request.get_json()
    if not data: return jsonify({"msg": "Request body tidak boleh kosong"}), 400
        
    identifier = data.get('identifier')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"msg": "Identifier dan password harus diisi"}), 400

    user = User.query.filter(
        ((User.email == identifier) | (User.username == identifier)),
        User.role == 'pasien'
    ).first()

    if user and user.check_password(password):
        expires = timedelta(days=1)
        access_token = create_access_token(
            identity={'id': user.id, 'username': user.username, 'role': user.role},
            expires_delta=expires
        )
        return jsonify(access_token=access_token, user=user.serialize_basic()), 200
    return jsonify({"msg": "Identifier atau password salah"}), 401

# --- Logout (Contoh Sederhana) ---
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Untuk implementasi blocklist token, perlu setup tambahan di Flask-JWT-Extended
    # Cara paling sederhana adalah client menghapus token.
    current_user_identity = get_jwt_identity()
    return jsonify(msg=f"User '{current_user_identity.get('username')}' logged out. Client harus menghapus token."), 200