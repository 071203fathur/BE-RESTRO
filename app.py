# BE-RESTRO/app.py

import os
from flask import Flask, send_from_directory 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi ekstensi di luar factory untuk akses global jika diperlukan di tempat lain,
# atau bisa juga di dalam factory jika hanya dipakai di sana.
# Untuk konsistensi dengan banyak pola Flask, kita definisikan di sini.
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    """Factory untuk membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)

    # --- KONFIGURASI APLIKASI ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False # Agar urutan field JSON sesuai definisi model jika memungkinkan
    
    # Base URL untuk file media (bisa dipisah per tipe jika perlu)
    app.config['MEDIA_BASE_URL'] = '/media/gerakan' 
    app.config['MEDIA_BASE_URL_PROFIL'] = '/media/profil/foto' # Untuk foto profil pasien

    # --- KONFIGURASI FILE UPLOAD ---
    # Base path untuk semua file yang di-upload
    upload_base_path = os.path.join(app.root_path, 'uploads')
    
    # Folder spesifik untuk upload file gerakan
    gerakan_upload_path = os.path.join(upload_base_path, 'gerakan')
    app.config['UPLOAD_FOLDER_FOTO'] = os.path.join(gerakan_upload_path, 'foto')
    app.config['UPLOAD_FOLDER_VIDEO'] = os.path.join(gerakan_upload_path, 'video')
    app.config['UPLOAD_FOLDER_MODEL'] = os.path.join(gerakan_upload_path, 'model_tflite')
    
    # Folder spesifik untuk upload foto profil pasien (jika diimplementasikan)
    profil_pasien_foto_path = os.path.join(upload_base_path, 'profil_pasien', 'foto')
    app.config['UPLOAD_FOLDER_PROFIL_FOTO'] = profil_pasien_foto_path
    
    # Ekstensi file yang diizinkan
    app.config['ALLOWED_EXTENSIONS_FOTO'] = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['ALLOWED_EXTENSIONS_VIDEO'] = {'mp4', 'mov', 'avi', 'mkv'}
    app.config['ALLOWED_EXTENSIONS_MODEL'] = {'tflite'}
    
    # Batas ukuran file upload (contoh: 100MB)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  
    
    # Pastikan semua folder untuk upload sudah ada saat aplikasi dimulai
    os.makedirs(app.config['UPLOAD_FOLDER_FOTO'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_VIDEO'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_MODEL'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_PROFIL_FOTO'], exist_ok=True)

    # --- INISIALISASI EKSTENSI DENGAN APLIKASI ---
    db.init_app(app)
    migrate.init_app(app, db) # Inisialisasi Flask-Migrate
    jwt.init_app(app)
    bcrypt.init_app(app)
    # Mengizinkan CORS untuk semua rute dari semua domain (cocok untuk development)
    # Untuk produksi, batasi origins jika perlu: origins=["http://domain-frontend-anda.com"]
    cors.init_app(app, resources={r"/*": {"origins": "*"}}) 

    # --- Konteks Aplikasi untuk Import Model dan Registrasi Blueprint ---
    with app.app_context():
        # 1. Import semua model agar dikenali oleh Flask-Migrate dan bisa digunakan
        from models import User, PatientProfile, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil

        # 2. Import semua blueprint (rute)
        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp
        from routes.gerakan_routes import gerakan_bp
        from routes.program_routes import program_bp
        from routes.laporan_routes import laporan_bp
        from routes.monitoring_routes import monitoring_bp
        from routes.terapis_routes import terapis_bp # Blueprint untuk endpoint terapis

        # 3. Daftarkan semua blueprint ke aplikasi dengan prefix URL masing-masing
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api/patient') # Prefix lebih spesifik
        app.register_blueprint(gerakan_bp, url_prefix='/api/gerakan')
        app.register_blueprint(program_bp, url_prefix='/api/program')
        app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        app.register_blueprint(terapis_bp, url_prefix='/api/terapis') # Registrasi blueprint terapis

        # 4. Rute untuk Health Check / Tes Koneksi Awal
        @app.route('/')
        def hello():
            return "API Backend Aplikasi Kesehatan (BE-RESTRO) v2.1 berjalan! Database: restro_db. Semua fitur aktif."

        # 5. Rute untuk menyajikan file-file yang di-upload
        # Endpoint ini akan diakses oleh frontend/mobile app untuk menampilkan/mengunduh file
        
        # Contoh URL: http://127.0.0.1:5001/media/gerakan/foto/namafileunik.jpg
        @app.route('/media/gerakan/foto/<path:filename>')
        def serve_gerakan_foto(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER_FOTO'], filename)

        # Contoh URL: http://127.0.0.1:5001/media/gerakan/video/namafileunik.mp4
        @app.route('/media/gerakan/video/<path:filename>')
        def serve_gerakan_video(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER_VIDEO'], filename)

        # Contoh URL: http://127.0.0.1:5001/media/gerakan/model_tflite/namafileunik.tflite
        @app.route('/media/gerakan/model_tflite/<path:filename>')
        def serve_gerakan_model(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER_MODEL'], filename)
        
        # Opsional: Rute penyaji file foto profil pasien
        # Contoh URL: http://127.0.0.1:5001/media/profil/foto/namafileunik_profil.jpg
        @app.route('/media/profil/foto/<path:filename>')
        def serve_profil_pasien_foto(filename):
            return send_from_directory(app.config['UPLOAD_FOLDER_PROFIL_FOTO'], filename)

        return app

# Membuat instance aplikasi menggunakan factory
# Ini penting agar perintah `flask run` dan `flask db` bisa menemukan `app`
app = create_app()

# Blok untuk menjalankan aplikasi secara langsung dengan `python app.py`
if __name__ == '__main__':
    # Ambil port dari variabel lingkungan APP_RUN_PORT atau default ke 5001
    port = int(os.environ.get("APP_RUN_PORT", 5001)) 
    # Debug mode akan aktif jika FLASK_DEBUG=1 di file .env
    app.run(port=port)
