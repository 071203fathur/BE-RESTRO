# BE-RESTRO/routes/gerakan_routes.py

from flask import Blueprint, request, jsonify, current_app
from models import db, Gerakan, AppUser
from flask_jwt_extended import jwt_required, get_jwt_identity
# Import helper Azure kita
from utils.azure_helpers import upload_file_to_blob, delete_blob
# Import helper GCS baru
from utils.gcs_helpers import upload_file_to_gcs, delete_file_from_gcs, trigger_vertex_ai_training, GCS_DESTINATION_FOLDER_MODELS, GCS_DESTINATION_FOLDER_RAW_VIDEOS
import uuid # Untuk membuat ID unik

gerakan_bp = Blueprint('gerakan_bp', __name__)

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
    model_file = request.files.get('model_tflite') # Ini akan diunggah ke GCS

    blob_name_foto, blob_name_video, gcs_uri_model = None, None, None
    
    try:
        # Upload foto dan video ke Azure Blob Storage
        if foto_file:
            blob_name_foto, err_foto = upload_file_to_blob(foto_file, 'gerakan/foto')
            if err_foto: raise Exception(f"Upload foto gagal: {err_foto}")
        
        if video_file:
            blob_name_video, err_video = upload_file_to_blob(video_file, 'gerakan/video')
            if err_video: raise Exception(f"Upload video gagal: {err_video}")

        # Upload model .tflite ke Google Cloud Storage
        if model_file:
            # Buat nama blob unik untuk model di GCS
            model_extension = model_file.filename.rsplit('.', 1)[1].lower()
            unique_model_filename = f"model_{uuid.uuid4().hex}.{model_extension}"
            gcs_destination_blob_name = f"{GCS_DESTINATION_FOLDER_MODELS}{unique_model_filename}"
            
            gcs_uri_model, err_model = upload_file_to_gcs(model_file, gcs_destination_blob_name, content_type='application/octet-stream')
            if err_model: raise Exception(f"Upload model TFLite gagal: {err_model}")

            # Pemicu Vertex AI training (opsional, tergantung implementasi)
            # Anda perlu mengisi project_id dan location yang sesuai
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "restro-462703") # Ganti dengan ID project Anda
            location = os.getenv("VERTEX_AI_LOCATION", "asia-southeast2") # Ganti dengan region yang sesuai
            
            # Jika video_file juga diunggah ke GCS untuk training Vertex AI
            # Anda bisa memicu training di sini
            # if video_file:
            #     # Pastikan video diunggah ke folder raw_videos di GCS untuk training
            #     video_extension = video_file.filename.rsplit('.', 1)[1].lower()
            #     unique_video_filename_for_training = f"video_{uuid.uuid4().hex}.{video_extension}"
            #     gcs_training_video_blob_name = f"{GCS_DESTINATION_FOLDER_RAW_VIDEOS}{unique_video_filename_for_training}"
            #     
            #     # Reset stream pointer for video_file if it was read previously
            #     video_file.seek(0) 
            #     gcs_video_training_uri, err_video_training = upload_file_to_gcs(video_file, gcs_training_video_blob_name, content_type=video_file.content_type)
            #     if err_video_training:
            #         current_app.logger.error(f"Gagal upload video untuk training Vertex AI: {err_video_training}")
            #         # Lanjutkan saja, atau berikan error jika training mutlak dibutuhkan
            #     else:
            #         trigger_vertex_ai_training(gcs_video_training_uri, str(uuid.uuid4()), nama_gerakan, project_id, location)


        # Buat entitas di database
        new_gerakan = Gerakan(
            nama_gerakan=nama_gerakan,
            deskripsi=deskripsi,
            blob_name_foto=blob_name_foto,
            blob_name_video=blob_name_video,
            gcs_uri_model_tflite=gcs_uri_model, # Simpan URI GCS di sini
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
        if gcs_uri_model: delete_file_from_gcs(gcs_uri_model.split('/')[-1]) # Hanya kirim nama blob ke GCS helper
        
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
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id)
    
    gerakan.nama_gerakan = request.form.get('nama_gerakan', gerakan.nama_gerakan)
    gerakan.deskripsi = request.form.get('deskripsi', gerakan.deskripsi)

    # Dictionary untuk memproses file: (file_key_in_request, blob_attribute_in_model, subfolder_for_azure/gcs_folder, is_gcs_file)
    files_to_process = {
        'foto': ('blob_name_foto', 'gerakan/foto', False), # Azure
        'video': ('blob_name_video', 'gerakan/video', False), # Azure
        'model_tflite': ('gcs_uri_model_tflite', GCS_DESTINATION_FOLDER_MODELS, True) # GCS
    }

    try:
        for file_key, (blob_attr, storage_path, is_gcs_file) in files_to_process.items():
            if file_key in request.files:
                file_storage = request.files[file_key]
                new_blob_name_or_uri = None
                err = None

                if is_gcs_file:
                    model_extension = file_storage.filename.rsplit('.', 1)[1].lower()
                    unique_model_filename = f"model_{uuid.uuid4().hex}.{model_extension}"
                    gcs_destination_blob_name = f"{storage_path}{unique_model_filename}"
                    new_blob_name_or_uri, err = upload_file_to_gcs(file_storage, gcs_destination_blob_name, content_type='application/octet-stream')
                else: # Azure Blob
                    new_blob_name_or_uri, err = upload_file_to_blob(file_storage, storage_path)
                
                if err:
                    raise Exception(f"Gagal upload {file_key}: {err}")
                
                # Hapus blob lama jika ada
                old_blob_value = getattr(gerakan, blob_attr)
                if old_blob_value:
                    if is_gcs_file:
                        delete_file_from_gcs(old_blob_value.split('/')[-1]) # Hanya kirim nama blob GCS
                    else:
                        delete_blob(old_blob_value) # Azure
                
                # Set atribut dengan nama blob/uri baru
                setattr(gerakan, blob_attr, new_blob_name_or_uri)
        
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
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    gerakan = Gerakan.query.get_or_404(gerakan_id)

    # Simpan nama blob/URI sebelum object dihapus dari session
    blob_foto = gerakan.blob_name_foto
    blob_video = gerakan.blob_name_video
    gcs_uri_model = gerakan.gcs_uri_model_tflite # Ambil URI GCS

    try:
        db.session.delete(gerakan)
        db.session.commit()

        # Hapus file dari Azure Blob Storage setelah commit DB berhasil
        if blob_foto: delete_blob(blob_foto)
        if blob_video: delete_blob(blob_video)
        # Hapus file dari GCS
        if gcs_uri_model: delete_file_from_gcs(gcs_uri_model.split('/')[-1]) # Hanya kirim nama blob GCS

        return jsonify({"msg": "Gerakan berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal menghapus gerakan {gerakan_id}: {str(e)}")
        return jsonify({"msg": "Gagal menghapus gerakan", "error": str(e)}), 500
