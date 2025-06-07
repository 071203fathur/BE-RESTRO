# BE-RESTRO/utils/azure_helpers.py

import os
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient
from flask import current_app

def _get_blob_service_client():
    """Membuat dan mengembalikan client untuk Azure Blob Service."""
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    if not connect_str:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")
    return BlobServiceClient.from_connection_string(connect_str)

def get_blob_url(blob_name):
    """
    Membangun URL publik lengkap untuk sebuah blob.
    Contoh blob_name: 'gerakan/foto/abcdef123.jpg'
    """
    if not blob_name:
        return None
    
    storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')

    if not storage_account_name or not container_name:
        # Mengembalikan None atau URL placeholder jika konfigurasi tidak ada
        current_app.logger.warning("AZURE_STORAGE_ACCOUNT_NAME or AZURE_STORAGE_CONTAINER_NAME is not set.")
        return None

    return f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}"

def upload_file_to_blob(file_storage, subfolder_path):
    """
    Mengunggah file ke subfolder tertentu di Azure Blob Storage.
    :param file_storage: Objek file dari request.files.
    :param subfolder_path: Path tujuan di dalam container, contoh: 'gerakan/foto' atau 'profil/foto'.
    :return: Tuple (nama_blob, error_message). nama_blob adalah path lengkap di container.
    """
    if not file_storage or not file_storage.filename:
        return None, "No file selected for upload."

    try:
        blob_service_client = _get_blob_service_client()
        container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')

        # Membuat nama file yang unik untuk menghindari konflik
        extension = file_storage.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        
        # Menggabungkan subfolder dengan nama file unik
        # Contoh: 'gerakan/foto/abcdef123.jpg'
        blob_name = f"{subfolder_path}/{unique_filename}"

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Mengunggah file
        file_storage.seek(0) # Pastikan membaca dari awal
        blob_client.upload_blob(file_storage.read(), blob_properties={'content_type': file_storage.content_type})

        # Mengembalikan path lengkap di dalam container
        return blob_name, None

    except Exception as e:
        current_app.logger.error(f"Failed to upload to Azure Blob Storage: {str(e)}")
        return None, f"Failed to upload file to cloud storage: {str(e)}"

def delete_blob(blob_name):
    """
    Menghapus sebuah blob dari Azure Blob Storage.
    :param blob_name: Path lengkap blob di dalam container, contoh: 'gerakan/foto/abcdef123.jpg'.
    :return: True jika berhasil, False jika gagal.
    """
    if not blob_name:
        return True # Anggap berhasil jika tidak ada yang perlu dihapus

    try:
        blob_service_client = _get_blob_service_client()
        container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.delete_blob()
        return True

    except Exception as e:
        # Jika file tidak ditemukan, itu bukan error kritis.
        if "BlobNotFound" in str(e):
             current_app.logger.warning(f"Blob '{blob_name}' not found for deletion, but proceeding.")
             return True
        current_app.logger.error(f"Failed to delete blob '{blob_name}': {str(e)}")
        return False
