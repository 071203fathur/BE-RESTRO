# BE-RESTRO/models.py

from app import db, bcrypt # Import db dan bcrypt dari app.py
from datetime import datetime, date # Untuk tanggal lahir dan timestamp
from sqlalchemy.orm import validates # Untuk validasi sederhana
import enum # Untuk Enum status program
import os # Untuk mengelola path file

# --- Enum untuk Status Program ---
class ProgramStatus(str, enum.Enum):
    BELUM_DIMULAI = "belum_dimulai"
    BERJALAN = "berjalan" 
    SELESAI = "selesai"
    DIBATALKAN = "dibatalkan"

# --- Model User ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nama_lengkap = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, index=True)  # 'terapis' atau 'pasien'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient_profile = db.relationship('PatientProfile', back_populates='user', uselist=False, cascade="all, delete-orphan")
    # program_dibuat (oleh terapis) & program_diterima (oleh pasien) didefinisikan di ProgramRehabilitasi
    # laporan_rehabilitasi_pasien & laporan_rehabilitasi_terapis didefinisikan di LaporanRehabilitasi

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

# --- Model PatientProfile ---
class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    jenis_kelamin = db.Column(db.String(20), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    tempat_lahir = db.Column(db.String(100), nullable=True)
    nomor_telepon = db.Column(db.String(20), nullable=True, unique=True) # nomor telepon unik
    alamat = db.Column(db.Text, nullable=True)
    nama_pendamping = db.Column(db.String(120), nullable=True)
    
    diagnosis = db.Column(db.String(255), nullable=True) # Untuk halaman monitoring
    catatan_tambahan = db.Column(db.Text, nullable=True) # Untuk halaman monitoring

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
            'diagnosis': self.diagnosis,
            'catatan_tambahan': self.catatan_tambahan,
            'tinggi_badan': self.tinggi_badan,
            'berat_badan': self.berat_badan,
            'golongan_darah': self.golongan_darah,
            'riwayat_medis': self.riwayat_medis,
            'riwayat_alergi': self.riwayat_alergi,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<PatientProfile for User ID: {self.user_id}>'

# --- Model Gerakan ---
class Gerakan(db.Model):
    __tablename__ = 'gerakan'

    id = db.Column(db.Integer, primary_key=True)
    nama_gerakan = db.Column(db.String(150), nullable=False, index=True)
    deskripsi = db.Column(db.Text, nullable=True)
    filename_foto = db.Column(db.String(255), nullable=True)
    filename_video = db.Column(db.String(255), nullable=True)
    filename_model_tflite = db.Column(db.String(255), nullable=True)
    created_by_terapis_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pembuat = db.relationship('User', foreign_keys=[created_by_terapis_id])

    def get_file_url(self, file_type, app_config):
        filename = None
        folder_key_map = {
            'foto': 'UPLOAD_FOLDER_FOTO',
            'video': 'UPLOAD_FOLDER_VIDEO',
            'model_tflite': 'UPLOAD_FOLDER_MODEL'
        }
        default_folder_map = {
            'foto': 'uploads/gerakan/foto',
            'video': 'uploads/gerakan/video',
            'model_tflite': 'uploads/gerakan/model_tflite'
        }

        if file_type == 'foto': filename = self.filename_foto
        elif file_type == 'video': filename = self.filename_video
        elif file_type == 'model_tflite': filename = self.filename_model_tflite
        
        if filename:
            # Ambil path subfolder (foto, video, model_tflite) dari config
            # Bukan path lengkap, tapi hanya nama subfolder terakhirnya
            folder_config_key = folder_key_map.get(file_type)
            upload_folder_path = app_config.get(folder_config_key, default_folder_map.get(file_type))
            subfolder_name = os.path.basename(upload_folder_path) # Mengambil 'foto', 'video', atau 'model_tflite'

            base_url = app_config.get('MEDIA_BASE_URL', '/media/gerakan') 
            return f"{base_url}/{subfolder_name}/{filename}"
        return None

    def serialize_simple(self):
        return {"id": self.id, "nama_gerakan": self.nama_gerakan}
        
    def serialize_full(self, app_config):
        pembuat_info = self.pembuat.serialize_basic() if self.pembuat else None
        return {
            "id": self.id,
            "nama_gerakan": self.nama_gerakan,
            "deskripsi": self.deskripsi,
            "url_foto": self.get_file_url('foto', app_config),
            "url_video": self.get_file_url('video', app_config),
            "url_model_tflite": self.get_file_url('model_tflite', app_config),
            "created_by_terapis": pembuat_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    def __repr__(self):
        return f'<Gerakan {self.nama_gerakan}>'

# --- Model ProgramRehabilitasi ---
class ProgramRehabilitasi(db.Model):
    __tablename__ = 'program_rehabilitasi'

    id = db.Column(db.Integer, primary_key=True)
    nama_program = db.Column(db.String(150), nullable=False)
    tanggal_program = db.Column(db.Date, nullable=False, default=date.today) # default ke hari ini
    catatan_terapis = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(ProgramStatus), nullable=False, default=ProgramStatus.BELUM_DIMULAI, index=True)
    terapis_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    pasien_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    detail_gerakan = db.relationship('ProgramGerakanDetail', backref='program', lazy='dynamic', cascade="all, delete-orphan")
    terapis = db.relationship('User', foreign_keys=[terapis_id], backref="program_dibuat")
    pasien = db.relationship('User', foreign_keys=[pasien_id], backref="program_diterima")
    # laporan_hasil (one-to-one dengan LaporanRehabilitasi) didefinisikan di LaporanRehabilitasi

    def serialize_simple(self):
        return {
            "id": self.id,
            "nama_program": self.nama_program,
            "tanggal_program": self.tanggal_program.isoformat() if self.tanggal_program else None,
            "terapis_id": self.terapis_id,
            "pasien_id": self.pasien_id,
            "status": self.status.value if self.status else None
        }

    def serialize_full(self, app_config):
        list_gerakan_details = []
        for detail in self.detail_gerakan.order_by(ProgramGerakanDetail.urutan.asc(), ProgramGerakanDetail.id.asc()).all():
            gerakan_obj = Gerakan.query.get(detail.gerakan_id) # Pastikan Gerakan diimport
            if gerakan_obj:
                gerakan_data = gerakan_obj.serialize_full(app_config)
                gerakan_data['jumlah_repetisi_direncanakan'] = detail.jumlah_repetisi # Nama field lebih jelas
                gerakan_data['urutan_dalam_program'] = detail.urutan
                # Tambahkan ID detail program untuk referensi di laporan
                gerakan_data['program_gerakan_detail_id'] = detail.id 
                list_gerakan_details.append(gerakan_data)
        
        terapis_info = self.terapis.serialize_basic() if self.terapis else None
        pasien_info = self.pasien.serialize_basic() if self.pasien else None

        return {
            "id": self.id,
            "nama_program": self.nama_program,
            "tanggal_program": self.tanggal_program.isoformat() if self.tanggal_program else None,
            "catatan_terapis": self.catatan_terapis,
            "status": self.status.value if self.status else None,
            "terapis": terapis_info,
            "pasien": pasien_info,
            "list_gerakan_direncanakan": list_gerakan_details, # Nama field lebih jelas
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    def __repr__(self):
        return f'<ProgramRehabilitasi {self.nama_program} untuk Pasien ID: {self.pasien_id}>'

# --- Model ProgramGerakanDetail ---
class ProgramGerakanDetail(db.Model):
    __tablename__ = 'program_gerakan_detail' # Tabel detail untuk setiap gerakan dalam program
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program_rehabilitasi.id', ondelete='CASCADE'), nullable=False)
    gerakan_id = db.Column(db.Integer, db.ForeignKey('gerakan.id', ondelete='CASCADE'), nullable=False) # Jika gerakan dihapus, detail ini juga hilang (CASCADE)
    jumlah_repetisi = db.Column(db.Integer, nullable=False)
    urutan = db.Column(db.Integer, nullable=True)

    gerakan = db.relationship('Gerakan') # Untuk akses mudah ke info gerakan

    @validates('jumlah_repetisi')
    def validate_repetisi(self, key, jumlah_repetisi):
        if not isinstance(jumlah_repetisi, int) or jumlah_repetisi <= 0:
            raise ValueError("Jumlah repetisi harus angka positif.")
        return jumlah_repetisi

    def serialize(self): # Serialisasi untuk ProgramGerakanDetail jika diperlukan terpisah
        gerakan_data = self.gerakan.serialize_simple() if self.gerakan else None
        return {
            "program_gerakan_detail_id": self.id,
            "program_id": self.program_id,
            "gerakan": gerakan_data,
            "jumlah_repetisi": self.jumlah_repetisi,
            "urutan": self.urutan
        }
    def __repr__(self):
        return f'<ProgramGerakanDetail: Gerakan ID {self.gerakan_id} untuk Program ID {self.program_id}>'


# --- Model LaporanRehabilitasi ---
class LaporanRehabilitasi(db.Model):
    __tablename__ = 'laporan_rehabilitasi'

    id = db.Column(db.Integer, primary_key=True)
    program_rehabilitasi_id = db.Column(db.Integer, db.ForeignKey('program_rehabilitasi.id', ondelete='SET NULL'), nullable=True, index=True)
    pasien_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    terapis_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    tanggal_laporan = db.Column(db.Date, nullable=False, default=date.today)
    total_waktu_rehabilitasi_detik = db.Column(db.Integer, nullable=True)
    catatan_pasien_laporan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pasien = db.relationship('User', foreign_keys=[pasien_id], backref='laporan_rehabilitasi_pasien')
    terapis_yang_assign = db.relationship('User', foreign_keys=[terapis_id], backref='laporan_rehabilitasi_terapis')
    program_asli = db.relationship('ProgramRehabilitasi', backref=db.backref('laporan_hasil', uselist=False, cascade="all, delete-orphan")) # Jika laporan dihapus, program tidak terpengaruh, tapi jika program dihapus, laporan bisa jadi yatim (SET NULL di FK)
    detail_hasil_gerakan = db.relationship('LaporanGerakanHasil', backref='laporan_induk', lazy='dynamic', cascade="all, delete-orphan")

    def format_durasi(self, total_detik):
        if total_detik is None or not isinstance(total_detik, (int, float)) or total_detik < 0:
            return "00:00" # Default jika tidak valid
        jam = int(total_detik // 3600)
        sisa_detik = int(total_detik % 3600)
        menit = int(sisa_detik // 60)
        detik = int(sisa_detik % 60)
        if jam > 0:
            return f"{jam:02d}:{menit:02d}:{detik:02d}"
        return f"{menit:02d}:{detik:02d}"

    def serialize_full(self, app_config):
        pasien_info = self.pasien.serialize_basic() if self.pasien else {}
        program_asli_info = self.program_asli.serialize_simple() if self.program_asli else {}
        
        detail_gerakan_list = []
        total_hitung_sempurna = 0
        total_hitung_tidak_sempurna = 0
        total_hitung_tidak_terdeteksi = 0

        for detail_hasil in self.detail_hasil_gerakan.order_by(LaporanGerakanHasil.urutan_gerakan_dalam_program.asc(), LaporanGerakanHasil.id.asc()).all():
            detail_gerakan_list.append(detail_hasil.serialize(app_config))
            total_hitung_sempurna += detail_hasil.jumlah_sempurna or 0
            total_hitung_tidak_sempurna += detail_hasil.jumlah_tidak_sempurna or 0
            total_hitung_tidak_terdeteksi += detail_hasil.jumlah_tidak_terdeteksi or 0
        
        nama_terapis_program = "N/A"
        if self.program_asli and self.program_asli.terapis:
            nama_terapis_program = self.program_asli.terapis.nama_lengkap

        return {
            "laporan_id": self.id,
            "pasien_info": pasien_info,
            "program_info": {
                "id": program_asli_info.get("id"),
                "nama_program": program_asli_info.get("nama_program"),
                "nama_terapis_program": nama_terapis_program,
            },
            "tanggal_program_direncanakan": program_asli_info.get("tanggal_program"),
            "tanggal_laporan_disubmit": self.tanggal_laporan.isoformat() if self.tanggal_laporan else None,
            "total_waktu_rehabilitasi_string": self.format_durasi(self.total_waktu_rehabilitasi_detik),
            "total_waktu_rehabilitasi_detik": self.total_waktu_rehabilitasi_detik,
            "catatan_pasien_laporan": self.catatan_pasien_laporan,
            "detail_hasil_gerakan": detail_gerakan_list,
            "summary_total_hitungan": {
                "sempurna": total_hitung_sempurna,
                "tidak_sempurna": total_hitung_tidak_sempurna,
                "tidak_terdeteksi": total_hitung_tidak_terdeteksi
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    def __repr__(self):
        return f'<LaporanRehabilitasi ID: {self.id} untuk Program ID: {self.program_rehabilitasi_id}>'

# --- Model LaporanGerakanHasil ---
class LaporanGerakanHasil(db.Model):
    __tablename__ = 'laporan_gerakan_hasil'

    id = db.Column(db.Integer, primary_key=True)
    laporan_rehabilitasi_id = db.Column(db.Integer, db.ForeignKey('laporan_rehabilitasi.id', ondelete='CASCADE'), nullable=False)
    gerakan_id = db.Column(db.Integer, db.ForeignKey('gerakan.id', ondelete='SET NULL'), nullable=True)
    program_gerakan_detail_id_asli = db.Column(db.Integer, db.ForeignKey('program_gerakan_detail.id', ondelete='SET NULL'), nullable=True)
    urutan_gerakan_dalam_program = db.Column(db.Integer, nullable=True)
    jumlah_sempurna = db.Column(db.Integer, default=0)
    jumlah_tidak_sempurna = db.Column(db.Integer, default=0)
    jumlah_tidak_terdeteksi = db.Column(db.Integer, default=0)
    waktu_aktual_per_gerakan_detik = db.Column(db.Integer, nullable=True)

    gerakan_asli = db.relationship('Gerakan')
    detail_program_asli = db.relationship('ProgramGerakanDetail') # Relasi ke rencana awal

    def format_durasi(self, total_detik):
        if total_detik is None or not isinstance(total_detik, (int,float)) or total_detik < 0:
            return "00:00"
        menit = int(total_detik // 60)
        detik = int(total_detik % 60)
        return f"{menit:02d}:{detik:02d}"

    def serialize(self, app_config):
        gerakan_info_full = self.gerakan_asli.serialize_full(app_config) if self.gerakan_asli else {}
        
        return {
            "laporan_gerakan_id": self.id,
            "gerakan_id_asli": self.gerakan_id,
            "nama_gerakan": gerakan_info_full.get("nama_gerakan", "Gerakan tidak ditemukan"),
            # Bisa sertakan URL foto/video gerakan jika UI laporan membutuhkannya per item
            # "url_foto_gerakan": gerakan_info_full.get("url_foto"), 
            "jumlah_repetisi_direncanakan": self.detail_program_asli.jumlah_repetisi if self.detail_program_asli else "N/A",
            "jumlah_sempurna": self.jumlah_sempurna,
            "jumlah_tidak_sempurna": self.jumlah_tidak_sempurna,
            "jumlah_tidak_terdeteksi": self.jumlah_tidak_terdeteksi,
            "waktu_aktual_per_gerakan_string": self.format_durasi(self.waktu_aktual_per_gerakan_detik),
            "waktu_aktual_per_gerakan_detik": self.waktu_aktual_per_gerakan_detik,
            "urutan_dalam_program": self.urutan_gerakan_dalam_program
        }
    def __repr__(self):
        return f'<LaporanGerakanHasil untuk Gerakan ID: {self.gerakan_id} di Laporan ID: {self.laporan_rehabilitasi_id}>'
