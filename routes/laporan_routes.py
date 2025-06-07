# BE-RESTRO/routes/laporan_routes.py
from flask import Blueprint, request, jsonify
from models import db, User, ProgramRehabilitasi, LaporanRehabilitasi, LaporanGerakanHasil, ProgramStatus, ProgramGerakanDetail
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
            if not gerakan_id:
                raise ValueError("Setiap item hasil harus memiliki 'gerakan_id'")

            detail_laporan = LaporanGerakanHasil(
                laporan_rehabilitasi_id=new_laporan.id,
                gerakan_id=gerakan_id,
                # ... (sisa field seperti jumlah_sempurna, dll.)
                jumlah_sempurna=item_hasil.get('jumlah_sempurna', 0),
                jumlah_tidak_sempurna=item_hasil.get('jumlah_tidak_sempurna', 0),
                jumlah_tidak_terdeteksi=item_hasil.get('jumlah_tidak_terdeteksi', 0),
            )
            db.session.add(detail_laporan)
        
        program_asli.status = ProgramStatus.SELESAI
        program_asli.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # DIUBAH: Menghapus parameter config
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
    # ... (logika otorisasi tetap sama) ...
    # DIUBAH: Menghapus parameter config
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
    
    # DIUBAH: Menghapus parameter config
    results = [l.serialize_full() for l in paginated_laporan.items]

    return jsonify({
        "laporan": results,
        "total_items": paginated_laporan.total,
        "total_pages": paginated_laporan.pages,
        "current_page": paginated_laporan.page
    }), 200

# Endpoint lainnya juga disesuaikan dengan cara yang sama
