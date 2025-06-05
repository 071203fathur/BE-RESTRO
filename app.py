# BE-RESTRO/app.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv

# Muat variabel lingkungan dari .env
load_dotenv()

# Inisialisasi ekstensi (tanpa app instance dulu)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    """Factory untuk membuat instance aplikasi Flask."""
    app = Flask(__name__)

    # Konfigurasi aplikasi
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') # Mengambil dari .env (menunjuk ke restro_db)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JSON_SORT_KEYS'] = False

    # Inisialisasi ekstensi dengan aplikasi
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}})


    # Import models di dalam context aplikasi
    with app.app_context():
        from models import User, PatientProfile

        # Import dan register Blueprints (rute)
        from routes.auth_routes import auth_bp
        from routes.patient_routes import patient_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/api')

        @app.route('/')
        def hello():
            return "API Backend Aplikasi Kesehatan (BE-RESTRO) berjalan! Database: restro_db"

        return app

app = create_app()

if __name__ == '__main__':
    # Port 5001 (atau sesuaikan jika perlu)
    app.run(port=5001)