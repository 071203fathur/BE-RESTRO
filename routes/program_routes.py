# BE-RESTRO/routes/program_routes.py
from flask import Blueprint, request, jsonify
from models import db, AppUser, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, ProgramStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime

program_bp = Blueprint('program_bp', __name__)

@program_bp.route('/pasien-list', methods=['GET'])
@jwt_required()
def get_pasien_list_for_terapis():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_list = AppUser.query.filter_by(role='pasien').order_by(AppUser.nama_lengkap.asc()).all()
    return jsonify([p.serialize_basic() for p in pasien_list]), 200


@program_bp.route('/', methods=['POST'])
@jwt_required()
def create_and_assign_program():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    data = request.get_json()
    nama_program = data.get('nama_program')
    pasien_id = data.get('pasien_id')
    list_gerakan_input = data.get('list_gerakan_direncanakan')
    tanggal_program_str = data.get('tanggal_program')
    catatan_terapis = data.get('catatan_terapis')
    status_program_str = data.get('status', ProgramStatus.BELUM_DIMULAI.value)

    if not all([nama_program, pasien_id, list_gerakan_input]):
        return jsonify({"msg": "Nama program, ID pasien, dan daftar gerakan wajib diisi"}), 400
    
    pasien = AppUser.query.filter_by(id=pasien_id, role='pasien').first_or_404("Pasien tidak ditemukan.")

    try:
        tanggal_program = datetime.strptime(tanggal_program_str, '%Y-%m-%d').date() if tanggal_program_str else date.today()
        status_program = ProgramStatus(status_program_str)
    except (ValueError, TypeError):
        return jsonify({"msg": "Format tanggal atau status tidak valid"}), 400

    new_program = ProgramRehabilitasi(
        nama_program=nama_program,
        tanggal_program=tanggal_program,
        catatan_terapis=catatan_terapis,
        status=status_program,
        terapis_id=current_user_identity.get('id'),
        pasien_id=pasien_id
    )
    
    try:
        db.session.add(new_program)
        db.session.flush()

        for idx, item_gerakan in enumerate(list_gerakan_input):
            gerakan_id = item_gerakan.get('gerakan_id')
            jumlah_repetisi = item_gerakan.get('jumlah_repetisi_direncanakan')
            urutan = item_gerakan.get('urutan_dalam_program', idx + 1)

            if not gerakan_id or not isinstance(jumlah_repetisi, int) or jumlah_repetisi <= 0:
                raise ValueError(f"Data gerakan tidak valid pada item {idx+1}")
            
            if not Gerakan.query.get(gerakan_id):
                 raise ValueError(f"Gerakan dengan ID {gerakan_id} tidak ditemukan")

            detail = ProgramGerakanDetail(
                program_id=new_program.id,
                gerakan_id=gerakan_id,
                jumlah_repetisi=jumlah_repetisi,
                urutan=urutan
            )
            db.session.add(detail)
        
        db.session.commit()
        # DIUBAH: Menghapus parameter config
        return jsonify({"msg": "Program berhasil dibuat", "program": new_program.serialize_full()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal membuat program", "error": str(e)}), 500


@program_bp.route('/pasien/today', methods=['GET'])
@jwt_required()
def get_program_pasien_today():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403

    pasien_id = current_user_identity.get('id')
    today = date.today()

    program = ProgramRehabilitasi.query.filter(
        ProgramRehabilitasi.pasien_id == pasien_id,
        ProgramRehabilitasi.tanggal_program <= today,
        ProgramRehabilitasi.status.in_([ProgramStatus.BELUM_DIMULAI, ProgramStatus.BERJALAN])
    ).order_by(ProgramRehabilitasi.tanggal_program.asc()).first()
    
    if not program:
        return jsonify({"msg": "Tidak ada program aktif yang dijadwalkan."}), 404
        
    # DIUBAH: Menghapus parameter config
    return jsonify(program.serialize_full()), 200


@program_bp.route('/pasien/history', methods=['GET'])
@jwt_required()
def get_program_history_pasien():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    paginated_programs = ProgramRehabilitasi.query.filter_by(pasien_id=pasien_id)\
        .order_by(ProgramRehabilitasi.tanggal_program.desc(), ProgramRehabilitasi.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # DIUBAH: Menghapus parameter config
    results = [p.serialize_full() for p in paginated_programs.items]

    return jsonify({
        "programs": results,
        "total_items": paginated_programs.total,
        "total_pages": paginated_programs.pages,
        "current_page": paginated_programs.page
    }), 200

# Endpoint lainnya juga disesuaikan dengan cara yang sama
@program_bp.route('/<int:program_id>', methods=['GET'])
@jwt_required()
def get_program_detail(program_id):
    program = ProgramRehabilitasi.query.get_or_404(program_id)
    # ... (logika otorisasi tetap sama) ...
    # DIUBAH: Menghapus parameter config
    return jsonify(program.serialize_full()), 200
