import logging
from uuid import UUID
from flask import Blueprint, request, jsonify
from src.util.middlewares.decorator_api import get_token_required_decorator
from src.domain.user.interface import IUser

# Catatan: Sesuaikan path import Interface/Service Anda jika diperlukan
# dari contoh: user_service akan mengeksekusi metode get(id: UUID)

logger = logging.getLogger(__name__)

def create_user_blueprint(user_service: IUser, secret_key: str, secret_api: str) -> Blueprint:
    user_controller = Blueprint('user', __name__)
    token_required = get_token_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────────────────────────────────
    # GET /user (Mengambil Data Profil User Berdasarkan JWT)
    # ──────────────────────────────────────────────────────────────────────
    @user_controller.route('/user', methods=['GET'])
    @token_required
    def get_user_profile():
        """
        Get current user profile details using JWT token
        ---
        tags:
          - User
        security:
          - Bearer: []
        responses:
          200:
            description: User data retrieved successfully
          401:
            description: Unauthorized - Token tidak valid atau user_id tidak ditemukan
          404:
            description: User tidak ditemukan
          400:
            description: Bad Request - Format UUID dari token tidak valid
          500:
            description: Terjadi kesalahan pada server
        """
        try:
            # Mengambil user_id dari claim JWT (mengikuti pola referensi Anda)
            user_id_str = request.current_user.get('user_id')
            if not user_id_str:
                return jsonify({
                    'success': False, 
                    'message': 'Akses ditolak, User ID tidak ditemukan dalam token'
                }), 401

            # Konversi string ID dari JWT ke format UUID
            user_id = UUID(user_id_str)

            # Panggil service/usecase layer yang memiliki fungsi get(id: UUID)
            user_response = user_service.get(id=user_id)

            # Jika user tidak ditemukan di database (return None dari fungsi get)
            if not user_response:
                return jsonify({
                    'success': False, 
                    'message': 'User tidak ditemukan'
                }), 404

            # Jika berhasil, kembalikan data dengan model_dump() (Pydantic v2)
            return jsonify({
                'success': True,
                'message': 'Berhasil mengambil data user',
                'data': user_response.model_dump()
            }), 200

        except ValueError as val_err:
            return jsonify({
                'success': False, 
                'message': f'Format User ID tidak valid: {str(val_err)}'
            }), 400
            
        except Exception as e:
            logger.error(f"[USER CONTROLLER] Gagal mengambil data user: {e}", exc_info=True)
            return jsonify({
                'success': False, 
                'message': 'Terjadi kesalahan pada server'
            }), 500

    return user_controller