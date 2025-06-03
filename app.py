import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv() # Muat variabel dari .env

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') # Mengambil dari .env
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Import Models (setelah db diinisialisasi) ---
from models import Produk # Kita akan buat models.py dengan class Produk

# --- Rute API Sederhana untuk Tes Awal ---
@app.route('/')
def hello():
    return "Selamat Datang di API Backend RESTRO!"

# --- (Opsional) Register Blueprints ---
# from routes.produk_routes import produk_bp # Contoh
# app.register_blueprint(produk_bp, url_prefix='/api')

# if __name__ == '__main__':
#     app.run()