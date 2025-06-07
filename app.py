# BE-RESTRO/app.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

# Inisialisasi ekstensi
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    """Factory untuk membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)

    # --- KONFIGURASI APLIKASI ---
    # Konfigurasi ini akan diambil dari Application Settings di Azure App Service
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # --- KONFIGURASI FILE UPLOAD (TIDAK DIPERLUKAN LAGI) ---
    # Semua konfigurasi UPLOAD_FOLDER, ALLOWED_EXTENSIONS, dan MAX_CONTENT_LENGTH
    # tidak lagi relevan karena file ditangani oleh Azure Blob Storage.
    # Batas ukuran file dan ekstensi akan divalidasi di dalam rute jika perlu.

    # --- INISIALISASI EKSTENSI DENGAN APLIKASI ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}) 

    # --- Konteks Aplikasi untuk Import Model dan Registrasi Blueprint ---
    with app.app_context():
        # 1. Import semua model agar dikenali oleh Flask-Migrate
        from models import User, PatientProfile, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil

        # 2. Import semua blueprint (rute)
        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp
        from routes.gerakan_routes import gerakan_bp
        from routes.program_routes import program_bp
        from routes.laporan_routes import laporan_bp
        from routes.monitoring_routes import monitoring_bp
        from routes.terapis_routes import terapis_bp

        # 3. Daftarkan semua blueprint
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api/patient')
        app.register_blueprint(gerakan_bp, url_prefix='/api/gerakan')
        app.register_blueprint(program_bp, url_prefix='/api/program')
        app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        app.register_blueprint(terapis_bp, url_prefix='/api/terapis')

        # 4. Rute untuk Health Check
        @app.route('/')
        def hello():
            return "API Backend BE-RESTRO v3.0 (Azure Ready) berjalan! Terhubung ke Azure services."

        # 5. Rute untuk menyajikan file (TIDAK DIPERLUKAN LAGI)
        # File akan disajikan langsung dari URL publik Azure Blob Storage.
        # Menghapus rute-rute send_from_directory().

        return app

# Membuat instance aplikasi untuk digunakan oleh Gunicorn/Flask CLI
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("APP_RUN_PORT", 5001))
    app.run(port=port)
