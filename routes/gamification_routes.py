# BE-RESTRO/routes/gamification_routes.py
# Modul baru untuk mengelola endpoint gamifikasi (leaderboard dan badge).
# PERBAIKAN: Mengatasi AttributeError: 'InstrumentedList' object has no attribute 'join'
# dengan melakukan query pada UserBadge.

from flask import Blueprint, jsonify, request, current_app
from models import db, AppUser, Badge, UserBadge
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc
from utils.azure_helpers import upload_file_to_blob, delete_blob # Untuk upload/hapus gambar badge
import uuid

gamification_bp = Blueprint('gamification_bp', __name__)

# --- ENDPOINT UNTUK LEADERBOARD ---
@gamification_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """
    Endpoint untuk mendapatkan leaderboard pasien berdasarkan total poin.
    Dapat diakses oleh terapis dan pasien.
    """
    current_user_identity = get_jwt_identity()
    # Anda bisa menambahkan otorisasi di sini jika hanya role tertentu yang boleh melihat
    # if current_user_identity.get('role') not in ['pasien', 'terapis']:
    #     return jsonify({"msg": "Akses ditolak"}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # Default 10 top users

    # Mengambil pasien dengan role 'pasien' dan mengurutkan berdasarkan total_points
    paginated_leaderboard = AppUser.query.filter_by(role='pasien') \
                                        .order_by(desc(AppUser.total_points)) \
                                        .paginate(page=page, per_page=per_page, error_out=False)

    results = []
    for user in paginated_leaderboard.items:
        # PERBAIKAN: Mengambil badge tertinggi yang dimiliki user.
        # Kita perlu query dari UserBadge, join ke Badge, lalu filter berdasarkan user.id
        highest_badge_entry = UserBadge.query.filter_by(user_id=user.id)\
                                             .join(Badge)\
                                             .order_by(desc(Badge.point_threshold))\
                                             .first()

        results.append({
            "user_id": user.id,
            "username": user.username,
            "nama_lengkap": user.nama_lengkap,
            "total_points": user.total_points,
            # Pastikan highest_badge_entry dan highest_badge_entry.badge ada sebelum diserialisasi
            "highest_badge_info": highest_badge_entry.badge.serialize() if highest_badge_entry and highest_badge_entry.badge else None,
        })

    return jsonify({
        "leaderboard": results,
        "total_items": paginated_leaderboard.total,
        "total_pages": paginated_leaderboard.pages,
        "current_page": paginated_leaderboard.page
    }), 200

# --- ENDPOINT UNTUK MANAJEMEN BADGE (OLEH TERAPIS/ADMIN) ---
@gamification_bp.route('/badges', methods=['POST'])
@jwt_required()
def create_badge():
    """
    Endpoint untuk terapis membuat badge baru.
    Membutuhkan nama, deskripsi, ambang batas poin, dan file gambar.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis': # Hanya terapis yang bisa membuat badge
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa membuat badge"}), 403

    name = request.form.get('name')
    description = request.form.get('description')
    point_threshold_str = request.form.get('point_threshold')
    badge_image_file = request.files.get('image')

    if not all([name, point_threshold_str]):
        return jsonify({"msg": "Nama badge dan ambang batas poin wajib diisi"}), 400
    
    try:
        point_threshold = int(point_threshold_str)
        if point_threshold < 0:
            return jsonify({"msg": "Ambang batas poin tidak boleh negatif"}), 400
    except ValueError:
        return jsonify({"msg": "Ambang batas poin harus berupa angka integer"}), 400

    if Badge.query.filter_by(name=name).first():
        return jsonify({"msg": "Nama badge sudah ada"}), 409
    if Badge.query.filter_by(point_threshold=point_threshold).first():
        return jsonify({"msg": "Ambang batas poin ini sudah digunakan oleh badge lain"}), 409

    filename_image = None
    if badge_image_file:
        try:
            # Menggunakan helper upload_file_to_blob dari azure_helpers.py
            # Subfolder: 'badges/'
            blob_name, err = upload_file_to_blob(badge_image_file, 'badges')
            if err:
                raise Exception(err)
            filename_image = blob_name
        except Exception as e:
            current_app.logger.error(f"Gagal upload gambar badge: {str(e)}")
            return jsonify({"msg": "Gagal mengunggah gambar badge", "error": str(e)}), 500

    new_badge = Badge(
        name=name,
        description=description,
        point_threshold=point_threshold,
        filename_image=filename_image
    )

    try:
        db.session.add(new_badge)
        db.session.commit()
        return jsonify({"msg": "Badge berhasil dibuat", "badge": new_badge.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        # Jika terjadi error setelah DB, hapus file yang mungkin sudah terupload
        if filename_image:
            delete_blob(filename_image)
        current_app.logger.error(f"Gagal membuat badge: {str(e)}")
        return jsonify({"msg": "Gagal membuat badge", "error": str(e)}), 500

@gamification_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_all_badges():
    """
    Endpoint untuk mendapatkan semua daftar badge yang tersedia.
    Dapat diakses oleh semua role yang terautentikasi.
    """
    badges = Badge.query.order_by(asc(Badge.point_threshold)).all()
    return jsonify({"badges": [b.serialize() for b in badges]}), 200

@gamification_bp.route('/badges/<int:badge_id>', methods=['GET'])
@jwt_required()
def get_badge_detail(badge_id):
    """
    Endpoint untuk mendapatkan detail badge spesifik.
    """
    badge = Badge.query.get_or_404(badge_id)
    return jsonify(badge.serialize()), 200

@gamification_bp.route('/badges/<int:badge_id>', methods=['PUT'])
@jwt_required()
def update_badge(badge_id):
    """
    Endpoint untuk terapis memperbarui detail badge yang sudah ada.
    Memungkinkan perubahan nama, deskripsi, ambang batas poin, dan gambar.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa memperbarui badge"}), 403

    badge = Badge.query.get_or_404(badge_id)

    name = request.form.get('name')
    description = request.form.get('description')
    point_threshold_str = request.form.get('point_threshold')
    badge_image_file = request.files.get('image')

    if name:
        if name != badge.name and Badge.query.filter_by(name=name).first():
            return jsonify({"msg": "Nama badge sudah ada"}), 409
        badge.name = name
    
    if description is not None: # Memungkinkan deskripsi dikosongkan
        badge.description = description

    if point_threshold_str:
        try:
            point_threshold = int(point_threshold_str)
            if point_threshold < 0:
                return jsonify({"msg": "Ambang batas poin tidak boleh negatif"}), 400
            if point_threshold != badge.point_threshold and Badge.query.filter_by(point_threshold=point_threshold).first():
                return jsonify({"msg": "Ambang batas poin ini sudah digunakan oleh badge lain"}), 409
            badge.point_threshold = point_threshold
        except ValueError:
            return jsonify({"msg": "Ambang batas poin harus berupa angka integer"}), 400

    old_filename_image = badge.filename_image
    if badge_image_file:
        try:
            blob_name, err = upload_file_to_blob(badge_image_file, 'badges')
            if err:
                raise Exception(err)
            badge.filename_image = blob_name
            # Hapus gambar lama jika berhasil upload yang baru
            if old_filename_image:
                delete_blob(old_filename_image)
        except Exception as e:
            current_app.logger.error(f"Gagal update gambar badge: {str(e)}")
            return jsonify({"msg": "Gagal mengupdate gambar badge", "error": str(e)}), 500
    elif 'image' in request.files and not badge_image_file: # Jika file 'image' dikirim tapi kosong (untuk hapus gambar)
        if old_filename_image:
            delete_blob(old_filename_image)
        badge.filename_image = None


    try:
        db.session.commit()
        return jsonify({"msg": "Badge berhasil diperbarui", "badge": badge.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal memperbarui badge {badge_id}: {str(e)}")
        return jsonify({"msg": "Gagal memperbarui badge", "error": str(e)}), 500

@gamification_bp.route('/badges/<int:badge_id>', methods=['DELETE'])
@jwt_required()
def delete_badge(badge_id):
    """
    Endpoint untuk terapis menghapus badge.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa menghapus badge"}), 403

    badge = Badge.query.get_or_404(badge_id)
    filename_to_delete = badge.filename_image

    try:
        db.session.delete(badge)
        db.session.commit()
        
        # Hapus file gambar dari Azure Blob Storage
        if filename_to_delete:
            delete_blob(filename_to_delete)

        return jsonify({"msg": "Badge berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Gagal menghapus badge {badge_id}: {str(e)}")
        return jsonify({"msg": "Gagal menghapus badge", "error": str(e)}), 500

# --- ENDPOINT UNTUK PASIEN MELIHAT BADGE MEREKA ---
@gamification_bp.route('/my-badges', methods=['GET'])
@jwt_required()
def get_my_badges():
    """
    Endpoint untuk pasien melihat daftar badge yang sudah mereka dapatkan.
    """
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    user_id = current_user_identity.get('id')
    user_badges = UserBadge.query.filter_by(user_id=user_id).all()

    badges_list = []
    for ub in user_badges:
        badges_list.append(ub.serialize())

    return jsonify({"my_badges": badges_list}), 200

