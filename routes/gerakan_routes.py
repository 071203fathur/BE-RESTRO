# BE-RESTRO/routes/gerakan_routes.py
import os
from flask import Blueprint, request, jsonify, current_app
from models import db, Gerakan, User # Pastikan User diimport jika digunakan untuk created_by
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import uuid # Untuk nama file unik

gerakan_bp = Blueprint('gerakan_bp', __name__)

def allowed_file(filename, allowed_extensions_key):
    """Memeriksa apakah ekstensi file diizinkan."""
    allowed_extensions = current_app.config.get(allowed_extensions_key)
    if not allowed_extensions: # Jika konfigurasi tidak ada
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file_to_folder(file, folder_type_key, allowed_extensions_key):
    """Menyimpan file ke folder yang sesuai dan mengembalikan nama file unik."""
    if not file or file.filename == '':
        return None, "Tidak ada file yang dipilih untuk diunggah."

    if not allowed_file(file.filename, allowed_extensions_key):
        allowed_ext_list = ', '.join(current_app.config.get(allowed_extensions_key, []))
        return None, f"Ekstensi file tidak diizinkan. Yang diizinkan: {allowed_ext_list}"

    upload_folder = current_app.config.get(folder_type_key)
    if not upload_folder:
        return None, "Konfigurasi folder upload tidak ditemukan."

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        file.save(file_path)
        return unique_filename, None  # Mengembalikan nama file, bukan path lengkap
    except Exception as e:
        # Log error e jika perlu
        return None, f"Gagal menyimpan file: {str(e)}"

@gerakan_bp.route('/', methods=['POST'])
@jwt_required()
def create_gerakan():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa membuat gerakan"}), 403

    if 'nama_gerakan' not in request.form:
        return jsonify({"msg": "Nama gerakan wajib diisi dalam form data"}), 400
    
    nama_gerakan = request.form.get('nama_gerakan')
    deskripsi = request.form.get('deskripsi')

    foto_file = request.files.get('foto')
    video_file = request.files.get('video')
    model_file = request.files.get('model_tflite')

    filename_foto, err_foto = save_file_to_folder(foto_file, 'UPLOAD_FOLDER_FOTO', 'ALLOWED_EXTENSIONS_FOTO') if foto_file else (None, None)
    filename_video, err_video = save_file_to_folder(video_file, 'UPLOAD_FOLDER_VIDEO', 'ALLOWED_EXTENSIONS_VIDEO') if video_file else (None, None)
    filename_model_tflite, err_model = save_file_to_folder(model_file, 'UPLOAD_FOLDER_MODEL', 'ALLOWED_EXTENSIONS_MODEL') if model_file else (None, None)
    
    errors = {}
    if err_foto: errors['foto'] = err_foto
    if err_video: errors['video'] = err_video
    if err_model: errors['model_tflite'] = err_model
    if errors:
        # Jika ada error upload, hapus file yang mungkin sudah ter-save sebagian
        if filename_foto: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_FOTO'], filename_foto))
        if filename_video: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_VIDEO'], filename_video))
        if filename_model_tflite: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_MODEL'], filename_model_tflite))
        return jsonify({"msg": "Gagal mengupload file", "errors": errors}), 400

    new_gerakan = Gerakan(
        nama_gerakan=nama_gerakan,
        deskripsi=deskripsi,
        filename_foto=filename_foto,
        filename_video=filename_video,
        filename_model_tflite=filename_model_tflite,
        created_by_terapis_id=current_user_identity.get('id')
    )

    try:
        db.session.add(new_gerakan)
        db.session.commit()
        # Menggunakan current_app.config untuk serialisasi URL file
        return jsonify({"msg": "Gerakan berhasil dibuat", "gerakan": new_gerakan.serialize_full(current_app.config)}), 201
    except Exception as e:
        db.session.rollback()
        # Hapus file jika commit DB gagal
        if filename_foto: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_FOTO'], filename_foto))
        if filename_video: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_VIDEO'], filename_video))
        if filename_model_tflite: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_MODEL'], filename_model_tflite))
        return jsonify({"msg": "Gagal membuat gerakan", "error": str(e)}), 500

@gerakan_bp.route('/', methods=['GET'])
@jwt_required() 
def get_all_gerakan():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', None, type=str)

    gerakan_query = Gerakan.query
    if search_term:
        gerakan_query = gerakan_query.filter(Gerakan.nama_gerakan.ilike(f"%{search_term}%"))
    
    gerakan_query = gerakan_query.order_by(Gerakan.nama_gerakan.asc())
    paginated_gerakan = gerakan_query.paginate(page=page, per_page=per_page, error_out=False)
    
    results = [g.serialize_full(current_app.config) for g in paginated_gerakan.items]
    
    return jsonify({
        "msg": "Daftar gerakan berhasil diambil",
        "gerakan": results,
        "total_items": paginated_gerakan.total,
        "total_pages": paginated_gerakan.pages,
        "current_page": paginated_gerakan.page,
        "per_page": paginated_gerakan.per_page
    }), 200

@gerakan_bp.route('/<int:gerakan_id>', methods=['GET'])
@jwt_required()
def get_gerakan_by_id(gerakan_id):
    gerakan = Gerakan.query.get_or_404(gerakan_id, description=f"Gerakan dengan ID {gerakan_id} tidak ditemukan.")
    return jsonify({"msg": "Detail gerakan berhasil diambil", "gerakan": gerakan.serialize_full(current_app.config)}), 200

@gerakan_bp.route('/<int:gerakan_id>', methods=['PUT'])
@jwt_required()
def update_gerakan(gerakan_id):
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id, description=f"Gerakan dengan ID {gerakan_id} tidak ditemukan.")
    # Optional: Cek jika terapis yang update adalah pembuatnya
    # if gerakan.created_by_terapis_id != current_user_identity.get('id'):
    #     return jsonify({"msg": "Anda tidak berhak mengubah gerakan ini"}), 403

    gerakan.nama_gerakan = request.form.get('nama_gerakan', gerakan.nama_gerakan)
    gerakan.deskripsi = request.form.get('deskripsi', gerakan.deskripsi)

    errors = {}
    files_to_update = {}

    if 'foto' in request.files:
        foto_file = request.files['foto']
        old_filename_foto = gerakan.filename_foto
        filename_foto, err_foto = save_file_to_folder(foto_file, 'UPLOAD_FOLDER_FOTO', 'ALLOWED_EXTENSIONS_FOTO')
        if err_foto: errors['foto'] = err_foto
        else: 
            files_to_update['filename_foto'] = filename_foto
            if old_filename_foto: 
                try: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_FOTO'], old_filename_foto))
                except OSError: pass # Abaikan jika file lama tidak ada atau gagal dihapus
    
    if 'video' in request.files:
        video_file = request.files['video']
        old_filename_video = gerakan.filename_video
        filename_video, err_video = save_file_to_folder(video_file, 'UPLOAD_FOLDER_VIDEO', 'ALLOWED_EXTENSIONS_VIDEO')
        if err_video: errors['video'] = err_video
        else:
            files_to_update['filename_video'] = filename_video
            if old_filename_video:
                try: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_VIDEO'], old_filename_video))
                except OSError: pass
    
    if 'model_tflite' in request.files:
        model_file = request.files['model_tflite']
        old_filename_model = gerakan.filename_model_tflite
        filename_model, err_model = save_file_to_folder(model_file, 'UPLOAD_FOLDER_MODEL', 'ALLOWED_EXTENSIONS_MODEL')
        if err_model: errors['model_tflite'] = err_model
        else:
            files_to_update['filename_model_tflite'] = filename_model
            if old_filename_model:
                try: os.remove(os.path.join(current_app.config['UPLOAD_FOLDER_MODEL'], old_filename_model))
                except OSError: pass

    if errors:
        return jsonify({"msg": "Gagal mengupdate file", "errors": errors}), 400

    for key, value in files_to_update.items():
        setattr(gerakan, key, value)
    
    gerakan.updated_at = db.func.now() # Update timestamp

    try:
        db.session.commit()
        return jsonify({"msg": "Gerakan berhasil diupdate", "gerakan": gerakan.serialize_full(current_app.config)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal mengupdate gerakan", "error": str(e)}), 500


@gerakan_bp.route('/<int:gerakan_id>', methods=['DELETE'])
@jwt_required()
def delete_gerakan(gerakan_id):
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id, description=f"Gerakan dengan ID {gerakan_id} tidak ditemukan.")
    # if gerakan.created_by_terapis_id != current_user_identity.get('id'):
    #     return jsonify({"msg": "Anda tidak berhak menghapus gerakan ini"}), 403

    filenames_to_delete = {
        'foto': (gerakan.filename_foto, current_app.config['UPLOAD_FOLDER_FOTO']),
        'video': (gerakan.filename_video, current_app.config['UPLOAD_FOLDER_VIDEO']),
        'model_tflite': (gerakan.filename_model_tflite, current_app.config['UPLOAD_FOLDER_MODEL'])
    }

    try:
        # Hapus relasi di ProgramGerakanDetail jika ada (tergantung ondelete setting di model)
        # Jika ondelete='CASCADE' di ProgramGerakanDetail.gerakan_id, ini tidak perlu
        # ProgramGerakanDetail.query.filter_by(gerakan_id=gerakan_id).delete()
        
        db.session.delete(gerakan)
        db.session.commit()

        for file_type, (filename, folder) in filenames_to_delete.items():
            if filename:
                try:
                    os.remove(os.path.join(folder, filename))
                except OSError:
                    pass # Abaikan jika file tidak ada atau gagal dihapus

        return jsonify({"msg": "Gerakan berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal menghapus gerakan", "error": str(e)}), 500

