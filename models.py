# BE-RESTRO/models.py

from app import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users' # Tabel ini akan dibuat di restro_db

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nama_lengkap = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'terapis' atau 'pasien'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient_profile = db.relationship('PatientProfile', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def serialize_basic(self):
        return {
            'id': self.id,
            'username': self.username,
            'nama_lengkap': self.nama_lengkap,
            'email': self.email,
            'role': self.role
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles' # Tabel ini akan dibuat di restro_db

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    jenis_kelamin = db.Column(db.String(20), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    tempat_lahir = db.Column(db.String(100), nullable=True)
    nomor_telepon = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    nama_pendamping = db.Column(db.String(120), nullable=True)
    
    tinggi_badan = db.Column(db.Integer, nullable=True)
    berat_badan = db.Column(db.Float, nullable=True)
    golongan_darah = db.Column(db.String(5), nullable=True)
    riwayat_medis = db.Column(db.Text, nullable=True)
    riwayat_alergi = db.Column(db.Text, nullable=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='patient_profile')

    def serialize_full(self):
        user_data = self.user.serialize_basic() if self.user else {}
        return {
            'user_id': self.user_id,
            'username': user_data.get('username'),
            'nama_lengkap': user_data.get('nama_lengkap'),
            'email': user_data.get('email'),
            'jenis_kelamin': self.jenis_kelamin,
            'tanggal_lahir': self.tanggal_lahir.isoformat() if self.tanggal_lahir else None,
            'tempat_lahir': self.tempat_lahir,
            'nomor_telepon': self.nomor_telepon,
            'alamat': self.alamat,
            'nama_pendamping': self.nama_pendamping,
            'tinggi_badan': self.tinggi_badan,
            'berat_badan': self.berat_badan,
            'golongan_darah': self.golongan_darah,
            'riwayat_medis': self.riwayat_medis,
            'riwayat_alergi': self.riwayat_alergi,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<PatientProfile for User ID: {self.user_id}>'