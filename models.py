# models.py
# TERBARU: Penambahan model PolaMakan dan penyesuaian relasi LaporanRehabilitasi.

from app import db, bcrypt
from datetime import datetime, date
from sqlalchemy.orm import validates
import enum
from utils.azure_helpers import get_blob_url

# Enum untuk Status Program
class ProgramStatus(str, enum.Enum):
    BELUM_DIMULAI = "belum_dimulai"
    BERJALAN = "berjalan"
    SELESAI = "selesai"
    DIBATALKAN = "dibatalkan"

# Model AppUser
class AppUser(db.Model):
    __tablename__ = 'app_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    nama_lengkap = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient_profile = db.relationship('PatientProfile', back_populates='user', uselist=False, cascade="all, delete-orphan")
    # Relasi ke PolaMakan yang dibuat oleh terapis
    pola_makan_dibuat = db.relationship('PolaMakan', foreign_keys='PolaMakan.terapis_id', backref='terapis_pembuat', lazy=True)
    # Relasi ke PolaMakan yang diterima oleh pasien
    pola_makan_diterima = db.relationship('PolaMakan', foreign_keys='PolaMakan.pasien_id', backref='pasien_penerima', lazy=True)

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

# Model PatientProfile
class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='CASCADE'), unique=True, nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    tempat_lahir = db.Column(db.String(100), nullable=True)
    nomor_telepon = db.Column(db.String(20), nullable=True, unique=True)
    alamat = db.Column(db.Text, nullable=True)
    nama_pendamping = db.Column(db.String(120), nullable=True)
    diagnosis = db.Column(db.String(255), nullable=True)
    catatan_tambahan = db.Column(db.Text, nullable=True)
    tinggi_badan = db.Column(db.Integer, nullable=True)
    berat_badan = db.Column(db.Float, nullable=True)
    golongan_darah = db.Column(db.String(5), nullable=True)
    riwayat_medis = db.Column(db.Text, nullable=True)
    riwayat_alergi = db.Column(db.Text, nullable=True)
    filename_foto_profil = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('AppUser', back_populates='patient_profile')

    def serialize_full(self):
        user_data = self.user.serialize_basic() if self.user else {}
        serialized_data = user_data.copy()
        serialized_data.update({
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
            'url_foto_profil': get_blob_url(self.filename_foto_profil),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        })
        return serialized_data

# Model Gerakan
class Gerakan(db.Model):
    __tablename__ = 'gerakan'
    id = db.Column(db.Integer, primary_key=True)
    nama_gerakan = db.Column(db.String(150), nullable=False, index=True)
    deskripsi = db.Column(db.Text, nullable=True)
    blob_name_foto = db.Column(db.String(255), nullable=True)
    blob_name_video = db.Column(db.String(255), nullable=True)
    blob_name_model_tflite = db.Column(db.String(255), nullable=True)
    created_by_terapis_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pembuat = db.relationship('AppUser', foreign_keys=[created_by_terapis_id])

    def serialize_simple(self):
        return {"id": self.id, "nama_gerakan": self.nama_gerakan}
        
    def serialize_full(self):
        pembuat_info = self.pembuat.serialize_basic() if self.pembuat else None
        return {
            "id": self.id,
            "nama_gerakan": self.nama_gerakan,
            "deskripsi": self.deskripsi,
            "url_foto": get_blob_url(self.blob_name_foto),
            "url_video": get_blob_url(self.blob_name_video),
            "url_model_tflite": get_blob_url(self.blob_name_model_tflite),
            "created_by_terapis": pembuat_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# Model ProgramRehabilitasi
class ProgramRehabilitasi(db.Model):
    __tablename__ = 'program_rehabilitasi'
    id = db.Column(db.Integer, primary_key=True)
    nama_program = db.Column(db.String(150), nullable=False)
    tanggal_program = db.Column(db.Date, nullable=False, default=date.today)
    catatan_terapis = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(ProgramStatus), nullable=False, default=ProgramStatus.BELUM_DIMULAI, index=True)
    terapis_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True)
    pasien_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    detail_gerakan = db.relationship('ProgramGerakanDetail', backref='program', lazy='dynamic', cascade="all, delete-orphan")
    terapis = db.relationship('AppUser', foreign_keys=[terapis_id], backref="program_dibuat")
    pasien = db.relationship('AppUser', foreign_keys=[pasien_id], backref="program_diterima")
    # Relasi ke LaporanRehabilitasi, menggunakan backref='program_rehab'
    laporan_hasil = db.relationship('LaporanRehabilitasi', backref='program_rehab', uselist=False, cascade="all, delete-orphan", primaryjoin="ProgramRehabilitasi.id == LaporanRehabilitasi.program_rehabilitasi_id")


    def serialize_simple(self):
        return {
            "id": self.id,
            "nama_program": self.nama_program,
            "tanggal_program": self.tanggal_program.isoformat() if self.tanggal_program else None,
            "status": self.status.value if self.status else None
        }

    def serialize_full(self):
        list_gerakan_direncanakan_details = []
        for detail in self.detail_gerakan.order_by(ProgramGerakanDetail.urutan.asc(), ProgramGerakanDetail.id.asc()).all():
            gerakan_obj = Gerakan.query.get(detail.gerakan_id)
            if gerakan_obj:
                gerakan_data = gerakan_obj.serialize_full()
                gerakan_data['jumlah_repetisi_direncanakan'] = detail.jumlah_repetisi
                gerakan_data['urutan_dalam_program'] = detail.urutan
                gerakan_data['program_gerakan_detail_id'] = detail.id
                list_gerakan_direncanakan_details.append(gerakan_data)
        
        terapis_info = self.terapis.serialize_basic() if self.terapis else None
        pasien_info = self.pasien.serialize_basic() if self.pasien else None

        laporan_terkait_summary = None
        if self.laporan_hasil:
            laporan_terkait_summary = {
                "laporan_id": self.laporan_hasil.id,
                "tanggal_laporan_disubmit": self.laporan_hasil.tanggal_laporan.isoformat() if self.laporan_hasil.tanggal_laporan else None,
                "total_waktu_rehabilitasi_string": self.laporan_hasil.format_durasi(self.laporan_hasil.total_waktu_rehabilitasi_detik),
                "total_waktu_rehabilitasi_detik": self.laporan_hasil.total_waktu_rehabilitasi_detik,
                "catatan_pasien_laporan": self.laporan_hasil.catatan_pasien_laporan,
                "detail_hasil_gerakan_aktual": []
            }
            for detail_hasil in self.laporan_hasil.detail_hasil_gerakan.order_by(LaporanGerakanHasil.urutan_gerakan_dalam_program.asc(), LaporanGerakanHasil.id.asc()).all():
                laporan_terkait_summary["detail_hasil_gerakan_aktual"].append(detail_hasil.serialize())
            
            total_sempurna = sum(d.jumlah_sempurna or 0 for d in self.laporan_hasil.detail_hasil_gerakan)
            total_tidak_sempurna = sum(d.jumlah_tidak_sempurna or 0 for d in self.laporan_hasil.detail_hasil_gerakan)
            total_tidak_terdeteksi = sum(d.jumlah_tidak_terdeteksi or 0 for d in self.laporan_hasil.detail_hasil_gerakan)
            laporan_terkait_summary["summary_total_hitungan_aktual"] = {
                "sempurna": total_sempurna,
                "tidak_sempurna": total_tidak_sempurna,
                "tidak_terdeteksi": total_tidak_terdeteksi
            }


        return {
            "id": self.id,
            "nama_program": self.nama_program,
            "tanggal_program": self.tanggal_program.isoformat() if self.tanggal_program else None,
            "catatan_terapis": self.catatan_terapis,
            "status": self.status.value if self.status else None,
            "terapis": terapis_info,
            "pasien": pasien_info,
            "list_gerakan_direncanakan": list_gerakan_direncanakan_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "laporan_terkait": laporan_terkait_summary
        }

# Model ProgramGerakanDetail
class ProgramGerakanDetail(db.Model):
    __tablename__ = 'program_gerakan_detail'
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program_rehabilitasi.id', ondelete='CASCADE'), nullable=False)
    gerakan_id = db.Column(db.Integer, db.ForeignKey('gerakan.id', ondelete='CASCADE'), nullable=False)
    jumlah_repetisi = db.Column(db.Integer, nullable=False)
    urutan = db.Column(db.Integer, nullable=True)
    gerakan = db.relationship('Gerakan')

# Model LaporanRehabilitasi
class LaporanRehabilitasi(db.Model):
    __tablename__ = 'laporan_rehabilitasi'
    id = db.Column(db.Integer, primary_key=True)
    program_rehabilitasi_id = db.Column(db.Integer, db.ForeignKey('program_rehabilitasi.id', ondelete='SET NULL'), nullable=True, index=True)
    pasien_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='CASCADE'), nullable=False, index=True)
    terapis_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True)
    tanggal_laporan = db.Column(db.Date, nullable=False, default=date.today)
    total_waktu_rehabilitasi_detik = db.Column(db.Integer, nullable=True)
    catatan_pasien_laporan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pasien = db.relationship('AppUser', foreign_keys=[pasien_id], backref='laporan_rehabilitasi_pasien')
    terapis_yang_assign = db.relationship('AppUser', foreign_keys=[terapis_id], backref='laporan_rehabilitasi_terapis')
    # program_asli = db.relationship('ProgramRehabilitasi', backref=db.backref('laporan_hasil', uselist=False, cascade="all, delete-orphan")) # Dihapus, diganti relationship di atas
    detail_hasil_gerakan = db.relationship('LaporanGerakanHasil', backref='laporan_induk', lazy='dynamic', cascade="all, delete-orphan")

    def format_durasi(self, total_detik):
        if total_detik is None: return "00:00"
        jam = int(total_detik // 3600)
        sisa_detik = int(total_detik % 3600)
        menit = int(sisa_detik // 60)
        detik = int(sisa_detik % 60)
        return f"{jam:02d}:{menit:02d}:{detik:02d}" if jam > 0 else f"{menit:02d}:{detik:02d}"

    def serialize_full(self):
        detail_gerakan_list = []
        for detail_hasil in self.detail_hasil_gerakan.order_by(LaporanGerakanHasil.urutan_gerakan_dalam_program.asc(), LaporanGerakanHasil.id.asc()).all():
            detail_gerakan_list.append(detail_hasil.serialize())
        
        pasien_info = self.pasien.serialize_basic() if self.pasien else {}
        program_asli_info = self.program_rehab.serialize_simple() if self.program_rehab else {} # Menggunakan program_rehab

        total_hitung_sempurna = sum(d['jumlah_sempurna'] for d in detail_gerakan_list)
        total_hitung_tidak_sempurna = sum(d['jumlah_tidak_sempurna'] for d in detail_gerakan_list)
        total_hitung_tidak_terdeteksi = sum(d['jumlah_tidak_terdeteksi'] for d in detail_gerakan_list)
        nama_terapis_program = self.program_rehab.terapis.nama_lengkap if self.program_rehab and self.program_rehab.terapis else "N/A" # Menggunakan program_rehab
        
        return {
            "laporan_id": self.id, "pasien_info": pasien_info,
            "program_info": {"id": program_asli_info.get("id"), "nama_program": program_asli_info.get("nama_program"), "nama_terapis_program": nama_terapis_program},
            "tanggal_program_direncanakan": program_asli_info.get("tanggal_program"),
            "tanggal_laporan_disubmit": self.tanggal_laporan.isoformat() if self.tanggal_laporan else None,
            "total_waktu_rehabilitasi_string": self.format_durasi(self.total_waktu_rehabilitasi_detik),
            "total_waktu_rehabilitasi_detik": self.total_waktu_rehabilitasi_detik,
            "catatan_pasien_laporan": self.catatan_pasien_laporan,
            "detail_hasil_gerakan": detail_gerakan_list,
            "summary_total_hitungan": {"sempurna": total_hitung_sempurna, "tidak_sempurna": total_hitung_tidak_sempurna, "tidak_terdeteksi": total_hitung_tidak_terdeteksi},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model LaporanGerakanHasil
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
    detail_program_asli = db.relationship('ProgramGerakanDetail')

    def serialize(self):
        gerakan_info = self.gerakan_asli.serialize_full() if self.gerakan_asli else {}
        return {
            "laporan_gerakan_id": self.id,
            "nama_gerakan": gerakan_info.get("nama_gerakan", "Gerakan tidak ditemukan"),
            "jumlah_repetisi_direncanakan": self.detail_program_asli.jumlah_repetisi if self.detail_program_asli else "N/A",
            "jumlah_sempurna": self.jumlah_sempurna,
            "jumlah_tidak_sempurna": self.jumlah_tidak_sempurna,
            "jumlah_tidak_terdeteksi": self.jumlah_tidak_terdeteksi,
            "waktu_aktual_per_gerakan_detik": self.waktu_aktual_per_gerakan_detik
        }

# NEW MODEL: PolaMakan
class PolaMakan(db.Model):
    __tablename__ = 'pola_makan'
    id = db.Column(db.Integer, primary_key=True)
    pasien_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='CASCADE'), nullable=False)
    terapis_id = db.Column(db.Integer, db.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True)
    tanggal_makan = db.Column(db.Date, nullable=False, index=True)
    menu_pagi = db.Column(db.Text, nullable=True)
    menu_siang = db.Column(db.Text, nullable=True)
    menu_malam = db.Column(db.Text, nullable=True)
    cemilan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def serialize(self):
        terapis_nama = self.terapis_pembuat.nama_lengkap if self.terapis_pembuat else "N/A"
        pasien_nama = self.pasien_penerima.nama_lengkap if self.pasien_penerima else "N/A"
        return {
            "id": self.id,
            "pasien_id": self.pasien_id,
            "nama_pasien": pasien_nama,
            "terapis_id": self.terapis_id,
            "nama_terapis": terapis_nama,
            "tanggal_makan": self.tanggal_makan.isoformat() if self.tanggal_makan else None,
            "menu_pagi": self.menu_pagi,
            "menu_siang": self.menu_siang,
            "menu_malam": self.menu_malam,
            "cemilan": self.cemilan,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
