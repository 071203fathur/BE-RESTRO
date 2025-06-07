# BE-RESTRO/routes/gerakan_routes.py

from flask import Blueprint, request, jsonify, current_app
from models import db, Gerakan, User
from flask_jwt_extended import jwt_required, get_jwt_identity
# Import helper Azure kita
from utils.azure_helpers import upload_file_to_blob, delete_blob

gerakan_bp = Blueprint('gerakan_bp', __name__)

# --- FUNGSI HELPER LOKAL DIHAPUS ---
# allowed_file dan save_file_to_folder tidak diperlukan lagi.

@gerakan_bp.route('', methods=['POST'])
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

    blob_name_foto, blob_name_video, blob_name_model = None, None, None
    
    try:
        # Upload file satu per satu dan simpan blob_name
        if foto_file:
            blob_name_foto, err_foto = upload_file_to_blob(foto_file, 'gerakan/foto')
            if err_foto: raise Exception(f"Upload foto gagal: {err_foto}")
        
        if video_file:
            blob_name_video, err_video = upload_file_to_blob(video_file, 'gerakan/video')
            if err_video: raise Exception(f"Upload video gagal: {err_video}")

        if model_file:
            blob_name_model, err_model = upload_file_to_blob(model_file, 'gerakan/model')
            if err_model: raise Exception(f"Upload model gagal: {err_model}")

        # Buat entitas di database
        new_gerakan = Gerakan(
            nama_gerakan=nama_gerakan,
            deskripsi=deskripsi,
            blob_name_foto=blob_name_foto,
            blob_name_video=blob_name_video,
            blob_name_model_tflite=blob_name_model,
            created_by_terapis_id=current_user_identity.get('id')
        )

        db.session.add(new_gerakan)
        db.session.commit()
        
        return jsonify({"msg": "Gerakan berhasil dibuat", "gerakan": new_gerakan.serialize_full()}), 201

    except Exception as e:
        db.session.rollback()
        # Jika terjadi error, hapus semua file yang mungkin sudah terupload
        if blob_name_foto: delete_blob(blob_name_foto)
        if blob_name_video: delete_blob(blob_name_video)
        if blob_name_model: delete_blob(blob_name_model)
        
        current_app.logger.error(f"Gagal membuat gerakan: {str(e)}")
        return jsonify({"msg": "Gagal membuat gerakan", "error": str(e)}), 500

@gerakan_bp.route('', methods=['GET'])
@jwt_required() 
def get_all_gerakan():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', None, type=str)

    query = Gerakan.query
    if search_term:
        query = query.filter(Gerakan.nama_gerakan.ilike(f"%{search_term}%"))
    
    paginated = query.order_by(Gerakan.nama_gerakan.asc()).paginate(page=page, per_page=per_page, error_out=False)
    results = [g.serialize_full() for g in paginated.items]
    
    return jsonify({
        "gerakan": results, "total_items": paginated.total,
        "total_pages": paginated.pages, "current_page": paginated.page
    })

@gerakan_bp.route('/<int:gerakan_id>', methods=['GET'])
@jwt_required()
def get_gerakan_by_id(gerakan_id):
    gerakan = Gerakan.query.get_or_404(gerakan_id)
    return jsonify(gerakan.serialize_full())

@gerakan_bp.route('/<int:gerakan_id>', methods=['PUT'])
@jwt_required()
def update_gerakan(gerakan_id):
    # (Kode otorisasi tetap sama)
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id)
    
    gerakan.nama_gerakan = request.form.get('nama_gerakan', gerakan.nama_gerakan)
    gerakan.deskripsi = request.form.get('deskripsi', gerakan.deskripsi)

    files_to_process = {
        'foto': ('blob_name_foto', 'gerakan/foto'),
        'video': ('blob_name_video', 'gerakan/video'),
        'model_tflite': ('blob_name_model_tflite', 'gerakan/model')
    }

    try:
        for file_key, (blob_attr, subfolder) in files_to_process.items():
            if file_key in request.files:
                file_storage = request.files[file_key]
                # Upload file baru
                new_blob_name, err = upload_file_to_blob(file_storage, subfolder)
                if err:
                    raise Exception(f"Gagal upload {file_key}: {err}")
                
                # Hapus blob lama jika ada
                old_blob_name = getattr(gerakan, blob_attr)
                if old_blob_name:
                    delete_blob(old_blob_name)
                
                # Set atribut dengan nama blob baru
                setattr(gerakan, blob_attr, new_blob_name)
        
        gerakan.updated_at = db.func.now()
        db.session.commit()
        return jsonify({"msg": "Gerakan berhasil diupdate", "gerakan": gerakan.serialize_full()}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal update gerakan {gerakan_id}: {str(e)}")
        return jsonify({"msg": "Gagal mengupdate gerakan", "error": str(e)}), 500

@gerakan_bp.route('/<int:gerakan_id>', methods=['DELETE'])
@jwt_required()
def delete_gerakan(gerakan_id):
    # (Kode otorisasi tetap sama)
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id)

    # Simpan nama blob sebelum object dihapus dari session
    blob_foto = gerakan.blob_name_foto
    blob_video = gerakan.blob_name_video
    blob_model = gerakan.blob_name_model_tflite

    try:
        db.session.delete(gerakan)
        db.session.commit()

        # Hapus file dari Azure Blob Storage setelah commit DB berhasil
        if blob_foto: delete_blob(blob_foto)
        if blob_video: delete_blob(blob_video)
        if blob_model: delete_blob(blob_model)

        return jsonify({"msg": "Gerakan berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal menghapus gerakan {gerakan_id}: {str(e)}")
        return jsonify({"msg": "Gagal menghapus gerakan", "error": str(e)}), 500
