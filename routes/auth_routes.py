# BE-RESTRO/routes/auth_routes.py
# PERUBAHAN FIREBASE: Menambahkan pembuatan/pengambilan pengguna Firebase dan token kustom
# saat login terapis dan pasien. Menambahkan endpoint untuk mendapatkan konfigurasi Firebase client-side.

from flask import Blueprint, request, jsonify, current_app
from models import AppUser, PatientProfile, db
from app import bcrypt # Import bcrypt dari app.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta 

# Import firebase_admin dan auth dari app.py setelah diinisialisasi
# Asumsi inisialisasi di app.py sudah global
from app import firebase_admin_initialized, FIREBASE_CLIENT_CONFIG
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError

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
        
        # --- Firebase User Provisioning for Terapis (saat register) ---
        if firebase_admin_initialized:
            try:
                # Membuat user Firebase dengan UID yang sama dengan ID user di DB utama
                firebase_user = auth.create_user(
                    uid=str(new_terapis.id),
                    display_name=new_terapis.nama_lengkap,
                    email=new_terapis.email
                )
                print(f"Firebase user created successfully for terapis ID: {new_terapis.id}")
            except Exception as e:
                # Log error, tapi jangan menghentikan registrasi utama jika Firebase gagal
                print(f"WARNING: Failed to create Firebase user for new terapis {new_terapis.id}: {str(e)}")
        # --- End Firebase User Provisioning ---

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
        
        firebase_custom_token = None
        if firebase_admin_initialized:
            try:
                # Dapatkan atau buat user Firebase
                uid_str = str(user.id)
                try:
                    firebase_user = auth.get_user(uid_str)
                except UserNotFoundError:
                    firebase_user = auth.create_user(uid=uid_str, display_name=user.nama_lengkap, email=user.email)
                
                # Buat custom token
                firebase_custom_token = auth.create_custom_token(firebase_user.uid).decode('utf-8')
            except Exception as e:
                print(f"ERROR_FIREBASE_LOGIN: Failed to handle Firebase user or custom token for terapis {user.id}: {e}")
                # Log error tapi jangan menghentikan proses login utama
        
        response_payload = {
            "access_token": access_token,
            "user": user.serialize_basic()
        }
        if firebase_custom_token:
            response_payload["firebase_custom_token"] = firebase_custom_token
            response_payload["firebase_client_config"] = FIREBASE_CLIENT_CONFIG # Kirim juga config
        
        return jsonify(response_payload), 200
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

    if AppUser.query.filter_by(username=username).first():
        return jsonify({"msg": "Username sudah terdaftar"}), 409
    if AppUser.query.filter_by(email=email).first():
        return jsonify({"msg": "Email sudah terdaftar"}), 409
    if nomor_telepon and PatientProfile.query.filter_by(nomor_telepon=nomor_telepon).first():
        return jsonify({"msg": "Nomor telepon sudah terdaftar"}), 409


    new_pasien_user = AppUser(
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
        
        # --- Firebase User Provisioning for Pasien (saat register) ---
        if firebase_admin_initialized:
            try:
                # Membuat user Firebase dengan UID yang sama dengan ID user di DB utama
                firebase_user = auth.create_user(
                    uid=str(new_pasien_user.id),
                    display_name=new_pasien_user.nama_lengkap,
                    email=new_pasien_user.email
                )
                print(f"Firebase user created successfully for pasien ID: {new_pasien_user.id}")
            except Exception as e:
                print(f"WARNING: Failed to create Firebase user for new pasien {new_pasien_user.id}: {str(e)}")
        # --- End Firebase User Provisioning ---

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

        firebase_custom_token = None
        if firebase_admin_initialized:
            try:
                # Dapatkan atau buat user Firebase
                uid_str = str(user.id)
                try:
                    firebase_user = auth.get_user(uid_str)
                except UserNotFoundError:
                    firebase_user = auth.create_user(uid=uid_str, display_name=user.nama_lengkap, email=user.email)
                
                # Buat custom token
                firebase_custom_token = auth.create_custom_token(firebase_user.uid).decode('utf-8')
            except Exception as e:
                print(f"ERROR_FIREBASE_LOGIN: Failed to handle Firebase user or custom token for pasien {user.id}: {e}")
                # Log error tapi jangan menghentikan proses login utama
        
        response_payload = {
            "access_token": access_token,
            "user": user.serialize_basic()
        }
        if firebase_custom_token:
            response_payload["firebase_custom_token"] = firebase_custom_token
            response_payload["firebase_client_config"] = FIREBASE_CLIENT_CONFIG # Kirim juga config
        
        return jsonify(response_payload), 200
    else:
        return jsonify({"msg": "Identifier atau password salah"}), 401

@auth_bp.route('/logout', methods=['POST'])
@jwt_required() 
def logout():
    current_user_identity = get_jwt_identity()
    return jsonify(msg=f"AppUser '{current_user_identity.get('username')}' logged out. Harap hapus token di sisi client."), 200

@auth_bp.route('/firebase-client-config', methods=['GET'])
def get_firebase_client_config():
    """
    Endpoint untuk mengembalikan konfigurasi Firebase client-side.
    Berguna untuk aplikasi mobile yang tidak menggunakan template HTML.
    """
    if not FIREBASE_CLIENT_CONFIG.get("apiKey"):
        return jsonify({"msg": "Firebase client configuration is not set up."}), 500
    return jsonify(FIREBASE_CLIENT_CONFIG), 200

