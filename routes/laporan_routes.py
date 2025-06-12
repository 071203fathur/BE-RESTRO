# BE-RESTRO/routes/laporan_routes.py
from flask import Blueprint, request, jsonify
from models import db, AppUser, ProgramRehabilitasi, LaporanRehabilitasi, LaporanGerakanHasil, ProgramStatus, ProgramGerakanDetail
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date

laporan_bp = Blueprint('laporan_bp', __name__)

@laporan_bp.route('/submit', methods=['POST']) 
@jwt_required()
def submit_laporan_rehabilitasi():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    pasien_id = current_user_identity.get('id')
    data = request.get_json()

    program_rehabilitasi_id = data.get('program_rehabilitasi_id')
    detail_hasil_input = data.get('detail_hasil_gerakan')

    if not program_rehabilitasi_id or not isinstance(detail_hasil_input, list):
        return jsonify({"msg": "program_rehabilitasi_id dan detail_hasil_gerakan wajib diisi"}), 400

    program_asli = ProgramRehabilitasi.query.get_or_404(program_rehabilitasi_id)
    if program_asli.pasien_id != pasien_id:
        return jsonify({"msg": "Anda tidak berhak mengirim laporan untuk program ini"}), 403
    
    if LaporanRehabilitasi.query.filter_by(program_rehabilitasi_id=program_rehabilitasi_id).first():
        return jsonify({"msg": "Laporan untuk program ini sudah pernah disubmit."}), 409

    new_laporan = LaporanRehabilitasi(
        program_rehabilitasi_id=program_rehabilitasi_id,
        pasien_id=pasien_id,
        terapis_id=program_asli.terapis_id,
        tanggal_laporan=date.today(),
        total_waktu_rehabilitasi_detik=data.get('total_waktu_rehabilitasi_detik'),
        catatan_pasien_laporan=data.get('catatan_pasien_laporan')
    )
    
    try:
        db.session.add(new_laporan)
        db.session.flush()

        for item_hasil in detail_hasil_input:
            gerakan_id = item_hasil.get('gerakan_id')
            program_gerakan_detail_id_asli = item_hasil.get('program_gerakan_detail_id_asli')
            urutan_gerakan_dalam_program = item_hasil.get('urutan_gerakan_dalam_program')
            waktu_aktual_per_gerakan_detik = item_hasil.get('waktu_aktual_per_gerakan_detik')

            if not gerakan_id:
                raise ValueError("Setiap item hasil harus memiliki 'gerakan_id'")

            detail_laporan = LaporanGerakanHasil(
                laporan_rehabilitasi_id=new_laporan.id,
                gerakan_id=gerakan_id,
                program_gerakan_detail_id_asli=program_gerakan_detail_id_asli,
                urutan_gerakan_dalam_program=urutan_gerakan_dalam_program,
                jumlah_sempurna=item_hasil.get('jumlah_sempurna', 0),
                jumlah_tidak_sempurna=item_hasil.get('jumlah_tidak_sempurna', 0),
                jumlah_tidak_terdeteksi=item_hasil.get('jumlah_tidak_terdeteksi', 0),
                waktu_aktual_per_gerakan_detik=waktu_aktual_per_gerakan_detik
            )
            db.session.add(detail_laporan)
        
        program_asli.status = ProgramStatus.SELESAI
        program_asli.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "msg": "Laporan berhasil disubmit", 
            "data_laporan": new_laporan.serialize_full()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal menyimpan laporan", "error": str(e)}), 500


@laporan_bp.route('/<int:laporan_id>', methods=['GET'])
@jwt_required()
def get_detail_laporan(laporan_id):
    laporan = LaporanRehabilitasi.query.get_or_404(laporan_id)
    current_user_identity = get_jwt_identity()
    user_role = current_user_identity.get('role')
    requesting_user_id = current_user_identity.get('id')

    # Otorisasi: Pasien hanya bisa melihat laporannya sendiri
    # Terapis bisa melihat laporan pasiennya jika dia adalah terapis yang meng-assign program
    # atau jika ingin terapis bisa melihat semua laporan (sesuaikan logika di sini)
    if user_role == 'pasien' and laporan.pasien_id != requesting_user_id:
        return jsonify({"msg": "Akses ditolak"}), 403
    elif user_role == 'terapis' and laporan.terapis_id != requesting_user_id and \
         not ProgramRehabilitasi.query.filter_by(id=laporan.program_rehabilitasi_id, terapis_id=requesting_user_id).first():
        # Opsional: Jika terapis bisa melihat laporan semua pasien (hapus kondisi `laporan.terapis_id != requesting_user_id`)
        return jsonify({"msg": "Akses ditolak: Anda tidak berhak melihat laporan ini."}), 403

    return jsonify(laporan.serialize_full()), 200


@laporan_bp.route('/pasien/history', methods=['GET'])
@jwt_required()
def get_laporan_history_pasien():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated_laporan = LaporanRehabilitasi.query.filter_by(pasien_id=pasien_id)\
        .order_by(LaporanRehabilitasi.tanggal_laporan.desc(), LaporanRehabilitasi.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    results = [l.serialize_full() for l in paginated_laporan.items]

    return jsonify({
        "laporan": results,
        "total_items": paginated_laporan.total,
        "total_pages": paginated_laporan.pages,
        "current_page": paginated_laporan.page
    }), 200

@laporan_bp.route('/terapis/by-pasien/<int:target_pasien_id>', methods=['GET'])
@jwt_required()
def get_laporan_history_by_pasien_for_terapis(target_pasien_id):
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    terapis_id = current_user_identity.get('id')

    # Periksa apakah terapis ini terkait dengan pasien melalui program
    # Atau jika terapis boleh melihat semua laporan (sesuaikan logika)
    pasien_user = AppUser.query.filter_by(id=target_pasien_id, role='pasien').first_or_404("Pasien tidak ditemukan.")
    
    # Otorisasi: Terapis hanya bisa melihat laporan dari pasien yang pernah di-assign program olehnya
    # Jika ingin terapis bisa melihat semua laporan pasien (hapus kondisi `ProgramRehabilitasi.terapis_id == terapis_id`)
    authorized_pasien = ProgramRehabilitasi.query.filter_by(pasien_id=target_pasien_id, terapis_id=terapis_id).first()
    if not authorized_pasien:
         return jsonify({"msg": f"Akses ditolak: Anda tidak memiliki program yang di-assign untuk pasien {pasien_user.nama_lengkap}."}), 403


    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated_laporan = LaporanRehabilitasi.query.filter_by(pasien_id=target_pasien_id)\
        .order_by(LaporanRehabilitasi.tanggal_laporan.desc(), LaporanRehabilitasi.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    results = [l.serialize_full() for l in paginated_laporan.items]

    return jsonify({
        "msg": f"Riwayat laporan untuk pasien {pasien_user.nama_lengkap} berhasil diambil",
        "laporan": results,
        "total_items": paginated_laporan.total,
        "total_pages": paginated_laporan.pages,
        "current_page": paginated_laporan.page
    }), 200
