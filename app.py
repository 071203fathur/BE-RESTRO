# BE-RESTRO/app.py

import os
from flask import Flask
from dotenv import load_dotenv

# 1. Import ekstensi dari file extensions.py BARU
from extensions import db, migrate, jwt, bcrypt, cors

def create_app():
    """Factory untuk membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)

    # --- KONFIGURASI APLIKASI ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # --- INISIALISASI EKSTENSI DENGAN APLIKASI ---
    # Inisialisasi terjadi di dalam factory
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}) 

    # --- Konteks Aplikasi untuk Import Model dan Registrasi Blueprint ---
    with app.app_context():
        # 2. Import semua model (nama AppUser sudah diubah)
        from models import AppUser, PatientProfile, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil

        # 3. Import semua blueprint
        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp
        from routes.gerakan_routes import gerakan_bp
        from routes.program_routes import program_bp
        from routes.laporan_routes import laporan_bp
        from routes.monitoring_routes import monitoring_bp
        from routes.terapis_routes import terapis_bp

        # 4. Daftarkan semua blueprint
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api/patient')
        app.register_blueprint(gerakan_bp, url_prefix='/api/gerakan')
        app.register_blueprint(program_bp, url_prefix='/api/program')
        app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        app.register_blueprint(terapis_bp, url_prefix='/api/terapis')

        # 5. Rute Health Check
        @app.route('/')
        def hello():
            return "API Backend BE-RESTRO v4.0 (Circular Import Fixed) berjalan!"

        return app

# Membuat instance aplikasi untuk Gunicorn/Flask CLI
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("APP_RUN_PORT", 5001))
    app.run(port=port)
