# utils/gcs_helpers.py
# Modul helper baru untuk interaksi dengan Google Cloud Storage dan Vertex AI.

from google.cloud import storage
import os
from flask import current_app # Diperlukan untuk logging

# --- Konfigurasi GCS ---
# Ganti dengan nama bucket GCS yang Anda gunakan untuk data training.
# Pastikan akun layanan (service account) yang digunakan oleh backend Flask Anda
# memiliki peran "Storage Object Admin" atau setidaknya "Storage Object Creator"
# pada bucket ini.
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "data-rehab-restro")

# Folder di dalam bucket yang akan menampung data input video untuk training.
# Contoh: "data_latihan_baru/raw_videos/"
GCS_DESTINATION_FOLDER_RAW_VIDEOS = os.getenv("GCS_RAW_VIDEOS_FOLDER", "data_training_raw_videos/")
GCS_DESTINATION_FOLDER_MODELS = os.getenv("GCS_MODELS_FOLDER", "trained_tflite_models/")


# Inisialisasi klien GCS.
# Library akan otomatis menggunakan kunci dari environment variable GOOGLE_APPLICATION_CREDENTIALS
# atau kredensial yang dikonfigurasi di lingkungan GCP.
try:
    storage_client = storage.Client()
except Exception as e:
    current_app.logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
    storage_client = None # Set to None if initialization fails

def upload_file_to_gcs(file_stream, destination_blob_name, content_type=None):
    """
    Fungsi untuk mengunggah file dari stream ke GCS.
    Digunakan untuk mengunggah model .tflite dari request.files.
    
    Args:
        file_stream: Objek file stream (misal: request.files['video']).
        destination_blob_name (str): Nama file tujuan lengkap di GCS (termasuk folder).
        content_type (str, optional): Tipe konten file (misal: 'video/mp4'). Default None.
    
    Returns:
        tuple: (URL_GCS_file, error_message)
    """
    if storage_client is None:
        return None, "Google Cloud Storage client not initialized. Check credentials."

    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        
        # Pastikan file stream berada di awal sebelum diunggah
        file_stream.seek(0)
        
        # Upload blob dengan content type yang benar
        blob.upload_from_file(file_stream, content_type=content_type)
        
        # Membuat URL yang dapat diakses publik (jika bucket dikonfigurasi untuk akses publik)
        # Atau URL yang ditandatangani jika akses publik tidak diinginkan.
        # Untuk tujuan ini, kita akan mengembalikan jalur gs://
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        current_app.logger.info(f"SUKSES: File '{destination_blob_name}' diunggah ke '{gcs_uri}'")
        return gcs_uri, None
    except Exception as e:
        current_app.logger.error(f"GAGAL: Upload ke GCS gagal. Error: {e}")
        return None, f"Gagal mengunggah file ke Google Cloud Storage: {str(e)}"

def delete_file_from_gcs(blob_name):
    """Menghapus sebuah blob dari Google Cloud Storage."""
    if storage_client is None:
        return False, "Google Cloud Storage client not initialized."
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()
        current_app.logger.info(f"SUKSES: File '{blob_name}' dihapus dari GCS.")
        return True, None
    except Exception as e:
        if "NotFound" in str(e): # Handle case where blob might not exist
            current_app.logger.warning(f"Blob '{blob_name}' not found for deletion, but proceeding.")
            return True, None
        current_app.logger.error(f"GAGAL: Menghapus file dari GCS gagal. Error: {e}")
        return False, f"Gagal menghapus file dari Google Cloud Storage: {str(e)}"

def get_gcs_url(blob_name):
    """Membangun URL publik untuk sebuah blob GCS."""
    if not blob_name:
        return None
    # Asumsi bucket public atau ada cara lain untuk mengakses (misal: signed URL)
    # Untuk tujuan ini, kita asumsikan dapat diakses secara publik
    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob_name}"


# Fungsi placeholder untuk memicu Vertex AI training (konseptual)
def trigger_vertex_ai_training(gcs_video_uri, training_id, model_name, project_id, location):
    """
    Fungsi placeholder untuk memicu training job di Vertex AI.
    Ini adalah bagian yang sangat kompleks dan memerlukan implementasi SDK Vertex AI
    serta training container/code yang sudah siap.
    
    Args:
        gcs_video_uri (str): URI GCS dari video input.
        training_id (str): ID unik untuk job training ini (misal: UUID gerakan).
        model_name (str): Nama model yang akan dilatih.
        project_id (str): ID project Google Cloud.
        location (str): Region Vertex AI (misal: 'asia-southeast2').
    
    Returns:
        tuple: (True/False, pesan_status)
    """
    current_app.logger.info(f"Memicu training Vertex AI untuk video: {gcs_video_uri}")
    current_app.logger.info(f"Dengan ID training: {training_id}, Model: {model_name}")
    current_app.logger.info("NOTE: Implementasi Vertex AI training SDK API yang sebenarnya akan dilakukan di sini.")
    
    try:
        # Contoh pseudo-code untuk memicu training job (membutuhkan instalasi google-cloud-aiplatform)
        # from google.cloud import aiplatform
        # aiplatform.init(project=project_id, location=location)
        #
        # # Asumsikan Anda punya CustomContainerTrainingJob atau CustomJob
        # # yang sudah mengacu pada Docker Image training Anda dan GCS path input/output
        # job = aiplatform.CustomContainerTrainingJob(
        #    display_name=f"gerakan-training-{model_name}-{training_id}",
        #    container_uri="gcr.io/your-project/your-training-image:latest", # Ganti dengan image training Anda
        #    command=["python", "train.py", "--input_video", gcs_video_uri, "--output_model_dir", f"gs://{GCS_BUCKET_NAME}/trained_models/"],
        #    # resource_pool=[{"machine_type": "n1-standard-4", "replica_count": 1}],
        # )
        #
        # model = job.run(
        #    # Asumsi ada skema input/output model yang cocok
        #    model_display_name=model_name,
        #    sync=False # Jangan sync agar tidak memblokir API response
        # )
        
        # Untuk demo dan mencegah dependency kompleks, kita hanya akan return sukses
        return True, "Training job Vertex AI berhasil dipicu (simulasi)."
    except Exception as e:
        current_app.logger.error(f"Gagal memicu training Vertex AI: {e}")
        return False, f"Gagal memicu training Vertex AI: {str(e)}"
