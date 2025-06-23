# BE-RESTRO/app.py
# PERUBAHAN: Menambahkan impor model PolaMakan dan gcs_helpers (melalui rute gerakan)
# PERUBAHAN BARU: Menambahkan impor mhodel Badge, UserBadge dan blueprint gamifikasi.
# PERUBAHAN FIREBASE: Menambahkan inisialisasi Firebase Admin SDK dan konfigurasi client-side.

import os
from flask import Flask
from dotenv import load_dotenv
import json # Diperlukan untuk mengurai JSON kredensial Firebase

# --- Import Firebase Admin SDK ---
import firebase_admin
from firebase_admin import credentials, auth

from extensions import db, migrate, jwt, bcrypt, cors

load_dotenv()

# Global flag untuk melacak status inisialisasi Firebase Admin SDK
firebase_admin_initialized = False

# Konfigurasi Firebase Client-Side (Client-side Firebase SDK)
# Ini adalah konfigurasi yang akan dikirim ke frontend.
# Anda bisa menemukannya di Firebase Console -> Project settings -> General -> Your apps -> Firebase SDK snippet (Config)
# Disarankan untuk mendapatkan nilai-nilai ini dari environment variables untuk keamanan
FIREBASE_CLIENT_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JSON_SORT_KEYS=False,
            JWT_DECODE_JSON=True
        )
    else:
        app.config.from_mapping(test_config)

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY tidak diatur di environment variables!")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    with app.app_context():
        # --- Konfigurasi Firebase Admin SDK di dalam app context ---
        # Mengambil konten JSON kredensial langsung dari environment variable
        FIREBASE_ADMIN_SDK_JSON_CONTENT = os.getenv('FIREBASE_ADMIN_SDK_JSON_CONTENT')

        global firebase_admin_initialized # Akses variabel global

        try:
            if not firebase_admin._apps: # Pastikan hanya diinisialisasi sekali
                if FIREBASE_ADMIN_SDK_JSON_CONTENT:
                    cred_dict = json.loads(FIREBASE_ADMIN_SDK_JSON_CONTENT)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK initialized successfully from environment variable in BE-RESTRO.")
                    firebase_admin_initialized = True
                else:
                    print("WARNING: FIREBASE_ADMIN_SDK_JSON_CONTENT environment variable not found. Firebase Admin SDK not initialized in BE-RESTRO.")
            else:
                print("Firebase Admin SDK already initialized in BE-RESTRO.")
                firebase_admin_initialized = True
        except json.JSONDecodeError as e:
            print(f"CRITICAL ERROR in BE-RESTRO: Failed to parse Firebase credentials JSON: {e}")
            firebase_admin_initialized = False
        except Exception as e:
            print(f"CRITICAL ERROR in BE-RESTRO: Error initializing Firebase Admin SDK: {e}")
            firebase_admin_initialized = False
        # --- Akhir Konfigurasi Firebase Admin SDK ---


        # Tambahkan PolaMakan, Badge, UserBadge ke daftar impor model
        from models import AppUser, PatientProfile, Gerakan, ProgramRehabilitasi, \
                           ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil, \
                           PolaMakan, Badge, UserBadge 

        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp
        from routes.gerakan_routes import gerakan_bp
        from routes.program_routes import program_bp
        from routes.laporan_routes import laporan_bp
        from routes.monitoring_routes import monitoring_bp
        from routes.terapis_routes import terapis_bp
        from routes.gamification_routes import gamification_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api/patient')
        app.register_blueprint(gerakan_bp, url_prefix='/api/gerakan')
        app.register_blueprint(program_bp, url_prefix='/api/program')
        app.register_blueprint(laporan_bp, url_prefix='/api/laporan')
        app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')
        app.register_blueprint(terapis_bp, url_prefix='/api/terapis')
        app.register_blueprint(gamification_bp, url_prefix='/api/gamification')

        @app.route('/')
        def hello():
            return "API Backend BE-RESTRO v4.2 (Config Refactored) berjalan!"

        return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("APP_RUN_PORT", 5001))
    app.run(port=port)
