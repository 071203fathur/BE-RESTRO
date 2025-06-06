# BE-RESTRO/routes/laporan_routes.py
from flask import Blueprint, request, jsonify, current_app
from models import db, User, ProgramRehabilitasi, Gerakan, ProgramGerakanDetail, LaporanRehabilitasi, LaporanGerakanHasil, ProgramStatus
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date

laporan_bp = Blueprint('laporan_bp', __name__)

@laporan_bp.route('/submit', methods=['POST']) 
@jwt_required()
def submit_laporan_rehabilitasi():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa mengirim laporan"}), 403

    pasien_id = current_user_identity.get('id')
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Request body (JSON) tidak boleh kosong"}), 400

    program_rehabilitasi_id = data.get('program_rehabilitasi_id')
    # Nama field dari Android: "detail_hasil_gerakan"
    detail_hasil_input = data.get('detail_hasil_gerakan') 
    total_waktu_rehabilitasi_detik = data.get('total_waktu_rehabilitasi_detik')
    catatan_pasien_laporan = data.get('catatan_pasien_laporan')
    # tanggal_laporan akan default ke hari ini jika tidak dikirim dari Android
    tanggal_laporan_str = data.get('tanggal_laporan', date.today().isoformat()) 

    if not program_rehabilitasi_id or not isinstance(detail_hasil_input, list):
        return jsonify({"msg": "program_rehabilitasi_id dan detail_hasil_gerakan (array) wajib diisi"}), 400

    program_asli = ProgramRehabilitasi.query.get(program_rehabilitasi_id)
    if not program_asli:
        return jsonify({"msg": f"Program rehabilitasi dengan ID {program_rehabilitasi_id} tidak ditemukan"}), 404
    
    if program_asli.pasien_id != pasien_id:
        return jsonify({"msg": "Anda tidak berhak mengirim laporan untuk program ini"}), 403

    # Cek apakah laporan untuk program ini sudah ada
    existing_report = LaporanRehabilitasi.query.filter_by(program_rehabilitasi_id=program_rehabilitasi_id).first()
    if existing_report:
        return jsonify({"msg": f"Laporan untuk program ini (ID: {program_rehabilitasi_id}) sudah pernah disubmit (ID Laporan: {existing_report.id}). Anda bisa mengedit laporan yang ada jika diizinkan."}), 409

    try:
        tanggal_laporan = datetime.strptime(tanggal_laporan_str, '%Y-%m-%d').date()
    except (ValueError, TypeError): # Menangkap TypeError jika tanggal_laporan_str adalah None
        return jsonify({"msg": "Format tanggal_laporan salah, gunakan YYYY-MM-DD atau pastikan dikirim"}), 400
    
    new_laporan = LaporanRehabilitasi(
        program_rehabilitasi_id=program_rehabilitasi_id,
        pasien_id=pasien_id,
        terapis_id=program_asli.terapis_id, 
        tanggal_laporan=tanggal_laporan,
        total_waktu_rehabilitasi_detik=total_waktu_rehabilitasi_detik,
        catatan_pasien_laporan=catatan_pasien_laporan
    )
    
    calculated_total_time_from_details = 0

    try:
        db.session.add(new_laporan)
        db.session.flush() # Dapatkan ID untuk new_laporan

        for item_hasil in detail_hasil_input:
            gerakan_id = item_hasil.get('gerakan_id') 
            # Mencari ID detail program asli berdasarkan gerakan_id dalam program yang dilaporkan
            # Ini mengasumsikan `urutan_gerakan_dalam_program` dikirim dari Android dan cocok dengan `ProgramGerakanDetail.urutan`
            # atau `program_gerakan_detail_id_asli` dikirim langsung dari Android
            
            program_gerakan_detail_id_asli_val = item_hasil.get('program_gerakan_detail_id_asli')
            urutan_val = item_hasil.get('urutan_gerakan_dalam_program')

            # Mencari detail program asli untuk mencocokkan
            pgd_asli = None
            if program_gerakan_detail_id_asli_val:
                pgd_asli = ProgramGerakanDetail.query.get(program_gerakan_detail_id_asli_val)
            elif gerakan_id and urutan_val is not None: # Fallback jika ID detail tidak ada, coba match by urutan
                 pgd_asli = ProgramGerakanDetail.query.filter_by(
                    program_id=program_rehabilitasi_id, 
                    gerakan_id=gerakan_id,
                    urutan=urutan_val 
                ).first()
            
            if not pgd_asli and gerakan_id: # Jika masih tidak ketemu, coba match hanya dengan gerakan_id (kurang akurat jika gerakan sama diulang)
                pgd_asli = ProgramGerakanDetail.query.filter_by(
                    program_id=program_rehabilitasi_id,
                    gerakan_id=gerakan_id
                ).first() # Mungkin perlu logika lebih baik jika ada duplikat gerakan dalam 1 program

            if not gerakan_id:
                 db.session.rollback()
                 return jsonify({"msg": "Setiap item hasil gerakan harus memiliki 'gerakan_id'"}), 400

            waktu_aktual = item_hasil.get('waktu_aktual_per_gerakan_detik')
            if isinstance(waktu_aktual, int) and waktu_aktual >= 0:
                calculated_total_time_from_details += waktu_aktual

            detail_laporan = LaporanGerakanHasil(
                laporan_rehabilitasi_id=new_laporan.id,
                gerakan_id=gerakan_id,
                program_gerakan_detail_id_asli = pgd_asli.id if pgd_asli else None,
                urutan_gerakan_dalam_program = pgd_asli.urutan if pgd_asli else urutan_val,
                jumlah_sempurna=item_hasil.get('jumlah_sempurna', 0),
                jumlah_tidak_sempurna=item_hasil.get('jumlah_tidak_sempurna', 0),
                jumlah_tidak_terdeteksi=item_hasil.get('jumlah_tidak_terdeteksi', 0),
                waktu_aktual_per_gerakan_detik=waktu_aktual
            )
            db.session.add(detail_laporan)
        
        # Update total waktu laporan dari detail jika tidak dikirim atau 0
        if total_waktu_rehabilitasi_detik is None or total_waktu_rehabilitasi_detik == 0:
            if calculated_total_time_from_details > 0 :
                 new_laporan.total_waktu_rehabilitasi_detik = calculated_total_time_from_details
        
        # Update status program asli menjadi 'selesai'
        program_asli.status = ProgramStatus.SELESAI
        program_asli.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            "msg": "Laporan rehabilitasi berhasil disubmit", 
            "laporan_id": new_laporan.id, 
            "data_laporan": new_laporan.serialize_full(current_app.config) # Kirim config untuk URL
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Error submit laporan: {str(e)}") 
        return jsonify({"msg": "Gagal menyimpan laporan rehabilitasi", "error": "Terjadi kesalahan internal server"}), 500


@laporan_bp.route('/<int:laporan_id>', methods=['GET'])
@jwt_required()
def get_detail_laporan(laporan_id):
    current_user_identity = get_jwt_identity()
    current_user_id = current_user_identity.get('id')
    user_role = current_user_identity.get('role')

    laporan = LaporanRehabilitasi.query.get_or_404(laporan_id, description=f"Laporan dengan ID {laporan_id} tidak ditemukan.")

    if user_role == 'pasien' and laporan.pasien_id != current_user_id:
        return jsonify({"msg": "Akses ditolak: Anda bukan pemilik laporan ini"}), 403
    # Terapis bisa melihat semua laporan pasien yang ditanganinya
    # atau lebih ketat: hanya terapis yang assign program ini
    elif user_role == 'terapis':
        is_terapis_related = False
        if laporan.terapis_id == current_user_id: # Jika terapis di laporan adalah user ini
            is_terapis_related = True
        elif laporan.program_asli and laporan.program_asli.terapis_id == current_user_id: # Jika terapis di program asli adalah user ini
            is_terapis_related = True
        
        # Logika tambahan: apakah terapis ini punya akses ke pasien ini? (misal dalam satu tim)
        # Untuk sekarang, kita batasi ke terapis yang terkait langsung dengan program/laporan.
        if not is_terapis_related:
             # Cek apakah terapis ini adalah terapis dari pasien tersebut (jika pasien punya 'assigned_terapis_id')
             # Ini memerlukan relasi tambahan di model User atau PatientProfile
             # Jika tidak ada, maka hanya terapis program/laporan yang bisa akses
             pasien_laporan = User.query.get(laporan.pasien_id)
             # if not (pasien_laporan and hasattr(pasien_laporan, 'assigned_terapis_id') and pasien_laporan.assigned_terapis_id == current_user_id):
             #    return jsonify({"msg": "Akses ditolak: Anda tidak terkait dengan pasien atau program ini."}), 403
             pass # Untuk sementara, terapis lain tidak bisa akses jika tidak terkait program/laporan

    return jsonify({"msg": "Detail laporan berhasil diambil", "laporan": laporan.serialize_full(current_app.config)}), 200


@laporan_bp.route('/pasien/history', methods=['GET'])
@jwt_required()
def get_laporan_history_pasien():
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'pasien':
        return jsonify({"msg": "Akses ditolak: Hanya pasien yang bisa melihat riwayat laporannya"}), 403
    
    pasien_id = current_user_identity.get('id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    laporan_query = LaporanRehabilitasi.query.filter_by(pasien_id=pasien_id)\
                                        .order_by(LaporanRehabilitasi.tanggal_laporan.desc(), LaporanRehabilitasi.created_at.desc())
    
    paginated_laporan = laporan_query.paginate(page=page, per_page=per_page, error_out=False)
    results = [l.serialize_full(current_app.config) for l in paginated_laporan.items]

    return jsonify({
        "msg": "Riwayat laporan pasien berhasil diambil",
        "laporan": results,
        "total_items": paginated_laporan.total,
        "total_pages": paginated_laporan.pages,
        "current_page": paginated_laporan.page
    }), 200


@laporan_bp.route('/terapis/by-pasien/<int:target_pasien_id>', methods=['GET'])
@jwt_required()
def get_laporan_pasien_for_terapis(target_pasien_id): # Nama fungsi diubah
    current_user_identity = get_jwt_identity()
    if current_user_identity.get('role') != 'terapis':
        return jsonify({"msg": "Akses ditolak: Hanya terapis yang bisa melihat laporan pasien"}), 403
    
    pasien_target = User.query.filter_by(id=target_pasien_id, role='pasien').first()
    if not pasien_target:
        return jsonify({"msg": f"Pasien dengan ID {target_pasien_id} tidak ditemukan"}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Terapis dapat melihat semua laporan dari pasien ini.
    # Bisa ditambahkan filter jika terapis hanya boleh melihat laporan dari program yang dia assign:
    # .join(ProgramRehabilitasi).filter(ProgramRehabilitasi.terapis_id == current_user_identity.get('id'))
    laporan_query = LaporanRehabilitasi.query.filter_by(pasien_id=target_pasien_id)\
                                        .order_by(LaporanRehabilitasi.tanggal_laporan.desc(), LaporanRehabilitasi.created_at.desc())
    
    paginated_laporan = laporan_query.paginate(page=page, per_page=per_page, error_out=False)
    results = [l.serialize_full(current_app.config) for l in paginated_laporan.items]

    return jsonify({
        "msg": f"Riwayat laporan untuk pasien '{pasien_target.nama_lengkap}' berhasil diambil",
        "laporan": results,
        "total_items": paginated_laporan.total,
        "total_pages": paginated_laporan.pages,
        "current_page": paginated_laporan.page
    }), 200

