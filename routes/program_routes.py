# BE-RESTRO/routes/program_routes.py
from flask import Blueprint, request, jsonify, current_app
from models import db, User, Gerakan, ProgramRehabilitasi, ProgramGerakanDetail, ProgramStatus # Import ProgramStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime, timedelta

program_bp = Blueprint('program_bp', __name__)

@program_bp.route('/pasien-list', methods=['GET'])
@jwt_required()
def get_pasien_list_for_terapis(): # Nama fungsi lebih deskriptif
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang dapat mengakses daftar pasien"}), 403
    
    # Mengambil pasien yang mungkin belum memiliki program, atau semua pasien
    # Ini bisa dioptimalkan lebih lanjut jika perlu
    pasien_list = User.query.filter_by(role='pasien').order_by(User.nama_lengkap.asc()).all()
    return jsonify([p.serialize_basic() for p in pasien_list]), 200


@program_bp.route('/', methods=['POST']) # Terapis membuat dan assign program
@jwt_required()
def create_and_assign_program():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa membuat program"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body tidak boleh kosong (JSON)"}), 400

    nama_program = data.get('nama_program')
    pasien_id = data.get('pasien_id')
    list_gerakan_input = data.get('list_gerakan_direncanakan') # Sesuai model: Array of {"gerakan_id": X, "jumlah_repetisi_direncanakan": Y, "urutan_dalam_program": Z}
    tanggal_program_str = data.get('tanggal_program') 
    catatan_terapis = data.get('catatan_terapis')
    status_program_str = data.get('status', ProgramStatus.BELUM_DIMULAI.value) # Default atau dari input

    if not all([nama_program, pasien_id, list_gerakan_input]):
        return jsonify({"msg": "Nama program, ID pasien, dan daftar gerakan wajib diisi"}), 400
    
    if not isinstance(list_gerakan_input, list) or not list_gerakan_input:
        return jsonify({"msg": "Daftar gerakan harus berupa array dan tidak boleh kosong"}), 400

    pasien = User.query.filter_by(id=pasien_id, role='pasien').first()
    if not pasien:
        return jsonify({"msg": f"Pasien dengan ID {pasien_id} tidak ditemukan atau bukan pasien"}), 404

    try:
        tanggal_program = datetime.strptime(tanggal_program_str, '%Y-%m-%d').date() if tanggal_program_str else date.today()
    except (ValueError, TypeError):
        return jsonify({"msg": "Format tanggal_program salah. Gunakan YYYY-MM-DD"}), 400
    
    try:
        status_program = ProgramStatus(status_program_str)
    except ValueError:
        return jsonify({"msg": f"Status program tidak valid. Pilihan: {', '.join([s.value for s in ProgramStatus])}"}), 400


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
        # Perlu flush agar new_program.id tersedia untuk ProgramGerakanDetail
        db.session.flush() 

        for idx, item_gerakan in enumerate(list_gerakan_input):
            gerakan_id = item_gerakan.get('gerakan_id')
            # Pastikan nama field di JSON request konsisten dengan yang diharapkan
            jumlah_repetisi = item_gerakan.get('jumlah_repetisi_direncanakan') 
            urutan = item_gerakan.get('urutan_dalam_program', idx + 1)

            if not gerakan_id or not isinstance(jumlah_repetisi, int) or jumlah_repetisi <= 0:
                db.session.rollback() 
                return jsonify({"msg": f"Data gerakan tidak valid pada item {idx+1}: 'gerakan_id' dan 'jumlah_repetisi_direncanakan' (positif) wajib"}), 400
            
            gerakan_obj = Gerakan.query.get(gerakan_id)
            if not gerakan_obj:
                db.session.rollback()
                return jsonify({"msg": f"Gerakan dengan ID {gerakan_id} tidak ditemukan pada item {idx+1}"}), 404

            detail = ProgramGerakanDetail(
                program_id=new_program.id, # Gunakan ID dari program yang baru di-flush
                gerakan_id=gerakan_id,
                jumlah_repetisi=jumlah_repetisi,
                urutan=urutan
            )
            db.session.add(detail)
        
        db.session.commit()
        return jsonify({"msg": "Program rehabilitasi berhasil dibuat dan di-assign", "program": new_program.serialize_full(current_app.config)}), 201
    
    except ValueError as ve: 
        db.session.rollback()
        return jsonify({"msg": f"Input tidak valid: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error membuat program: {str(e)}") # Logging server
        return jsonify({"msg": "Gagal membuat program rehabilitasi", "error": "Terjadi kesalahan internal server"}), 500


@program_bp.route('/pasien/today', methods=['GET']) # Pasien mengambil program hari ini
@jwt_required()
def get_program_pasien_today():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa mengambil program"}), 403

    pasien_id = current_user_identity.get('id')
    today = date.today()

    program = ProgramRehabilitasi.query.filter(
        ProgramRehabilitasi.pasien_id == pasien_id,
        ProgramRehabilitasi.tanggal_program <= today, # Program yang dijadwalkan hari ini atau sebelumnya
        ProgramRehabilitasi.status.in_([ProgramStatus.BELUM_DIMULAI, ProgramStatus.BERJALAN]) # Hanya yang belum atau sedang berjalan
    ).order_by(ProgramRehabilitasi.tanggal_program.asc(), ProgramRehabilitasi.created_at.asc()).first() # Ambil yang paling awal & belum selesai
    
    if not program:
        return jsonify({"msg": "Tidak ada program rehabilitasi aktif yang dijadwalkan untuk Anda hari ini atau sebelumnya."}), 404
        
    return jsonify({"msg": "Program rehabilitasi berhasil diambil", "program": program.serialize_full(current_app.config)}), 200


@program_bp.route('/pasien/history', methods=['GET'])
@jwt_required()
def get_program_history_pasien(): # Riwayat program yang telah/sedang dijalani pasien
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak"}), 403
    
    pasien_id = current_user_identity.get('id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # Default 10 program per halaman

    program_query = ProgramRehabilitasi.query.filter_by(pasien_id=pasien_id)\
                                          .order_by(ProgramRehabilitasi.tanggal_program.desc(), ProgramRehabilitasi.created_at.desc())
    
    paginated_programs = program_query.paginate(page=page, per_page=per_page, error_out=False)
    results = [p.serialize_full(current_app.config) for p in paginated_programs.items]

    return jsonify({
        "msg": "Riwayat program pasien berhasil diambil",
        "programs": results,
        "total_items": paginated_programs.total,
        "total_pages": paginated_programs.pages,
        "current_page": paginated_programs.page
    }), 200

@program_bp.route('/terapis/assigned-to-patient/<int:pasien_id>', methods=['GET']) # Terapis melihat program yang dia assign ke pasien tertentu
@jwt_required()
def get_programs_assigned_by_terapis_to_patient(pasien_id):
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak"}), 403

    terapis_id = current_user_identity.get('id')
    
    pasien_target = User.query.filter_by(id=pasien_id, role='pasien').first()
    if not pasien_target:
        return jsonify({"msg": f"Pasien dengan ID {pasien_id} tidak ditemukan."}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    program_query = ProgramRehabilitasi.query.filter_by(terapis_id=terapis_id, pasien_id=pasien_id)\
                                          .order_by(ProgramRehabilitasi.tanggal_program.desc(), ProgramRehabilitasi.created_at.desc())
    
    paginated_programs = program_query.paginate(page=page, per_page=per_page, error_out=False)
    results = [p.serialize_full(current_app.config) for p in paginated_programs.items]

    return jsonify({
        "msg": f"Daftar program yang di-assign ke pasien {pasien_target.nama_lengkap} berhasil diambil",
        "programs": results,
        "total_items": paginated_programs.total,
        "total_pages": paginated_programs.pages,
        "current_page": paginated_programs.page
    }), 200

@program_bp.route('/<int:program_id>', methods=['GET']) # Detail satu program (bisa diakses terapis pemilik atau pasien penerima)
@jwt_required()
def get_program_detail(program_id):
    current_user_identity = get_jwt_identity()
    user_id = current_user_identity.get('id')
    user_role = current_user_identity.get('role')

    program = ProgramRehabilitasi.query.get_or_404(program_id, description=f"Program dengan ID {program_id} tidak ditemukan.")

    if user_role == 'pasien' and program.pasien_id != user_id:
        return jsonify({"msg": "Akses ditolak: Anda bukan penerima program ini."}), 403
    elif user_role == 'terapis' and program.terapis_id != user_id:
        # Terapis mungkin ingin melihat program yang diassign ke pasiennya, meskipun bukan dia yg buat (jika ada tim terapis)
        # Untuk sekarang, kita batasi hanya terapis pembuat. Sesuaikan jika perlu.
        return jsonify({"msg": "Akses ditolak: Anda bukan pembuat program ini."}), 403

    return jsonify({"msg": "Detail program berhasil diambil", "program": program.serialize_full(current_app.config)}), 200


@program_bp.route('/<int:program_id>/update-status', methods=['PUT']) # Terapis atau sistem (misal saat pasien mulai) mengubah status program
@jwt_required()
def update_program_status(program_id):
    current_user_identity = get_jwt_identity()
    user_role = current_user_identity.get('role')

    program = ProgramRehabilitasi.query.get_or_404(program_id)

    # Logika otorisasi: Siapa yang boleh mengubah status?
    # Misal: Terapis pembuat, atau pasien bisa mengubah ke 'berjalan'
    if user_role == 'pasien' and program.pasien_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403
    elif user_role == 'terapis' and program.terapis_id != current_user_identity.get('id'):
        return jsonify({"msg": "Akses ditolak"}), 403
        
    data = request.get_json()
    new_status_str = data.get('status')

    if not new_status_str:
        return jsonify({"msg": "Status baru wajib diisi"}), 400

    try:
        new_status_enum = ProgramStatus(new_status_str)
    except ValueError:
        return jsonify({"msg": f"Status tidak valid. Pilihan: {', '.join([s.value for s in ProgramStatus])}"}), 400

    # Logika transisi status (opsional, tapi bagus untuk dimiliki)
    # Contoh: tidak bisa kembali ke 'belum_dimulai' jika sudah 'selesai'
    if program.status == ProgramStatus.SELESAI and new_status_enum != ProgramStatus.SELESAI:
        return jsonify({"msg": "Program yang sudah selesai tidak bisa diubah statusnya kecuali menjadi selesai lagi (jika ada koreksi)."}), 400
    
    program.status = new_status_enum
    program.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({"msg": f"Status program berhasil diubah menjadi '{new_status_enum.value}'", "program": program.serialize_simple()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Gagal mengubah status program", "error": str(e)}), 500

# Endpoint PUT dan DELETE untuk program bisa ditambahkan jika terapis diizinkan mengubah/menghapus program yang sudah di-assign
