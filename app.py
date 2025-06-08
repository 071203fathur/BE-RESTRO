# BE-RESTRO/app.py

import os
from flask import Flask
from dotenv import load_dotenv

# Import ekstensi dari file extensions.py
from extensions import db, migrate, jwt, bcrypt, cors

# Muat variabel lingkungan dari file .env
load_dotenv()

def create_app(test_config=None):
    """Factory untuk membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)

    # --- KONFIGURASI APLIKASI ---
    # Prioritaskan test_config jika ada (untuk testing)
    if test_config is None:
        # Konfigurasi default dari environment variables
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JSON_SORT_KEYS=False,
            # Memberitahu Flask-JWT-Extended untuk mengizinkan tipe data apa pun
            # (termasuk dictionary) sebagai identity di dalam token.
            JWT_DECODE_JSON=True
        )
    else:
        # Muat konfigurasi dari test_config
        app.config.from_mapping(test_config)

    # Memastikan JWT_SECRET_KEY ada, jika tidak, aplikasi akan gagal start
    # Ini membantu mendeteksi error konfigurasi lebih awal
    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY tidak diatur di environment variables!")

    # --- INISIALISASI EKSTENSI DENGAN APLIKASI ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}) 

    # --- Konteks Aplikasi untuk Import Model dan Registrasi Blueprint ---
    with app.app_context():
        from models import AppUser, PatientProfile, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil
        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp
        from routes.gerakan_routes import gerakan_bp
        from routes.program_routes import program_bp
        from routes.laporan_routes import laporan_bp
        from routes.monitoring_routes import monitoring_bp
        from routes.terapis_routes import terapis_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api/patient')
        app.register_blueprint(gerakan_bp, url_prefix='/api/gerakan')
        app.register_blueprint(program_bp, url_prefix='/api/program')
        app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        app.register_blueprint(terapis_bp, url_prefix='/api/terapis')

        @app.route('/')
        def hello():
            return "API Backend BE-RESTRO v4.2 (Config Refactored) berjalan!"

        return app

# Membuat instance aplikasi
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("APP_RUN_PORT", 5001))
    app.run(port=port)
