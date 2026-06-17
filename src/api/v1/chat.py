import logging
import json
from uuid import UUID
from flask import Blueprint, request, jsonify, Response, stream_with_context
from pydantic import ValidationError
from sqlalchemy.orm import Session

# Import Interfaces & DTOs
from src.domain.chat.interface import IChat
from src.domain.chat.model import ChatUpdateDTO, ChatGetAllDTO
from src.data.models.chats import ChatModel
from src.util.middlewares.decorator_api import get_token_required_decorator

logger = logging.getLogger(__name__)

def create_chat_blueprint(chat_service: IChat, secret_key: str, secret_api: str) -> Blueprint:
    chat_controller = Blueprint('chat', __name__)
    token_required = get_token_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────────────────────────────────
    # POST /chats
    # ──────────────────────────────────────────────────────────────────────
    # @chat_controller.route('/chats', methods=['POST'])
    # @token_required
    # def create_chat():
    #     """
    #     Create a new chat session with initial query
    #     ---
    #     tags:
    #       - Chat Session
    #     security:
    #       - Bearer: []
    #     parameters:
    #       - in: body
    #         name: body
    #         required: true
    #         schema:
    #           type: object
    #           required:
    #             - query
    #           properties:
    #             query:
    #               type: string
    #               example: "Dokter, saya merasa pusing di bagian belakang kepala sejak kemarin."
    #     responses:
    #       201:
    #         description: Chat session created successfully along with context
    #       400:
    #         description: Invalid JSON body
    #       422:
    #         description: Validation Error
    #       500:
    #         description: Internal Server Error
    #     """
    #     data = request.get_json(silent=True)
    #     if not data:
    #         return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

    #     query = data.get('query', '').strip()
    #     if not query:
    #         return jsonify({'success': False, 'message': 'Parameter query wajib diisi'}), 422

    #     try:
    #         # Mengambil user_id dari JWT context token dan divalidasi ke UUID
    #         user_id_str = request.current_user.get('user_id')
    #         user_id = UUID(user_id_str)

    #         # Memanggil service layer untuk pembuatan chat room baru & orkestrasi RAG LLM
    #         messages_response = chat_service.create_new_chat_session(user_id=user_id, query=query)
            
    #         return jsonify({
    #             'success': True,
    #             'message': 'Sesi chat baru berhasil dibuat',
    #             'data': [msg.model_dump() for msg in messages_response]
    #         }), 201

    #     except ValueError as val_err:
    #         return jsonify({'success': False, 'message': f'Format User ID tidak valid: {str(val_err)}'}), 422
    #     except Exception as e:
    #         logger.error(f"[CHAT CONTROLLER] Gagal membuat sesi chat baru: {e}", exc_info=True)
    #         return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    @chat_controller.route('/chats', methods=['POST'])
    @token_required
    def create_chat():
        """Create a new chat session with streaming architecture"""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        query = data.get('query', '').strip()
        if not query:
            return jsonify({'success': False, 'message': 'Parameter query wajib diisi'}), 422

        try:
            user_id_str = request.current_user.get('user_id')
            user_id = UUID(user_id_str)

            # 1. Jalankan Tahap Persiapan (Sinkronus)
            # Jika lolos guardrail, data chat_id & title langsung terbuat.
            chat_id, title, history_for_llm = chat_service.prepare_chat_session(user_id=user_id, query=query)
            
            # 2. Definisikan Generator untuk Flask HTTP Stream
            def generate_sse_stream():
                # Kirim info metadata di awal stream agar Frontend tahu Chat ID & Judul barunya
                metadata = {
                    "type": "metadata",
                    "chat_id": chat_id,
                    "title": title,
                    "success": True
                }
                yield f"data: {json.dumps(metadata)}\n\n"
                
                # Ambil chunk token dari service layer
                llm_stream = chat_service.stream_llm_and_save_assistant(
                    user_id=user_id, chat_id=chat_id, history_for_llm=history_for_llm
                )
                
                for token in llm_stream:
                    chunk_data = {
                        "type": "token",
                        "content": token
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

            # 3. Kembalikan Response dengan mimetype text/event-stream
            return Response(
                stream_with_context(generate_sse_stream()), 
                mimetype='text/event-stream'
            )

        except ValueError as val_err:
            # Menangkap error Guardrail Abort (422) sebelum stream dimulai
            return jsonify({'success': False, 'message': str(val_err)}), 422
            
        except Exception as e:
            logger.error(f"[CHAT CONTROLLER] Gagal membuat sesi chat baru: {e}", exc_info=True)
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # PATCH /chats/<chat_id> (Hanya Mengubah Title)
    # ──────────────────────────────────────────────────────────────────────
    @chat_controller.route('/chats/<string:chat_id>', methods=['PATCH'])
    @token_required
    def update_chat_title(chat_id: str):
        """
        Update chat room title only
        ---
        tags:
          - Chat Session
        security:
          - Bearer: []
        parameters:
          - in: path
            name: chat_id
            type: string
            required: true
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - title
              properties:
                title:
                  type: string
                  example: "Konsultasi Pusing Kepala Belakang"
        responses:
          200:
            description: Chat title updated successfully
          403:
            description: Forbidden - Bukan pemilik room chat
          404:
            description: Chat session tidak ditemukan
          422:
            description: Validation Error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'message': 'Parameter title wajib diisi'}), 422
        
        try:
            user_id_str = request.current_user.get('user_id')
            user_id = UUID(user_id_str)

            # Sesuai requirement: Hanya mengizinkan perubahan title dari API ini
            update_dto = ChatUpdateDTO(title=title)
            
            updated_chat = chat_service.update_chat_session(chat_id=chat_id, dto=update_dto, user_id=user_id)

            return jsonify({
                'success': True,
                'message': 'Judul chat berhasil diperbarui',
                'data': updated_chat.model_dump()
            }), 200

        except ValidationError as pydantic_err:
            return jsonify({
                'success': False, 
                'message': 'Validasi input gagal', 
                'errors': pydantic_err.errors(include_url=False)
            }), 422
        except Exception as e:
            logger.error(f"[CHAT CONTROLLER] Gagal memperbarui judul chat {chat_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500


    # ──────────────────────────────────────────────────────────────────────
    # POST /chats/<chat_id>/summary (Mengubah Desc via Generation Summary)
    # ──────────────────────────────────────────────────────────────────────
    @chat_controller.route('/chats/<string:chat_id>/summary', methods=['POST'])
    @token_required
    def generate_chat_description_summary(chat_id: str):
        """
        Generate and update chat description using auto LLM summarization
        ---
        tags:
          - Chat Session
        security:
          - Bearer: []
        parameters:
          - in: path
            name: chat_id
            type: string
            required: true
        responses:
          200:
            description: Chat description automatically summarized and updated
          403:
            description: Forbidden - Bukan pemilik room chat
          404:
            description: Chat session atau pesan pendukung tidak ditemukan
        """
        try:
            user_id_str = request.current_user.get('user_id')
            user_id = UUID(user_id_str)

            # Eksekusi fungsi rangkuman otomatis menggunakan LLM Service
            updated_chat_summary = chat_service.generate_chat_summary(chat_id=chat_id, user_id=user_id)

            return jsonify({
                'success': True,
                'message': 'Rangkuman deskripsi chat berhasil diperbarui otomatis',
                'data': updated_chat_summary.model_dump()
            }), 200

        except ValueError as val_err:
            # Menangani kondisi ketika chat room kosong / tidak ada pesan untuk dirangkum
            return jsonify({'success': False, 'message': str(val_err)}), 404
        except Exception as e:
            logger.error(f"[CHAT CONTROLLER] Gagal membuat rangkuman deskripsi chat {chat_id}: {e}", exc_info=True)
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'}), 500

    # ──────────────────────────────────────────────────────────────────────
    # GET /chats (Ambil Semua Sesi Chat User)
    # ──────────────────────────────────────────────────────────────────────
    @chat_controller.route('/chats', methods=['GET'])
    @token_required
    def get_all_chats():
        """
        Get all chat sessions for the authenticated user
        ---
        tags:
          - Chat Session
        security:
          - Bearer: []
        parameters:
          - in: query
            name: search
            type: string
            description: Cari berdasarkan judul atau deskripsi chat
          - in: query
            name: limit
            type: integer
            default: 10
          - in: query
            name: skip
            type: integer
            default: 0
          - in: query
            name: start_date
            type: string
            format: date-time
          - in: query
            name: end_date
            type: string
            format: date-time
        responses:
          200:
            description: Daftar sesi chat berhasil diambil
          422:
            description: Validasi query parameter gagal
          500:
            description: Terjadi kesalahan pada server
        """
        try:
            # Ambil user_id dari JWT context token
            user_id_str = request.current_user.get('user_id')
            user_id = UUID(user_id_str)

            # Ambil query params dari request.args dan bersihkan data kosong
            raw_params = {
                'search': request.args.get('search', '').strip() or None,
                'limit': request.args.get('limit', 10, type=int),
                'skip': request.args.get('skip', 0, type=int),
                'start_date': request.args.get('start_date') or None,
                'end_date': request.args.get('end_date') or None
            }

            # Validasi parameter menggunakan Pydantic DTO
            # Menyaring nilai yang None agar Pydantic menggunakan default value dari DTO
            clean_params = {k: v for k, v in raw_params.items() if v is not None}
            model_dto = ChatGetAllDTO(**clean_params)

            # Panggil service layer
            chats_response = chat_service.get_all_chat(user_id=user_id, model=model_dto)

            return jsonify({
                'success': True,
                'message': 'Daftar sesi chat berhasil diambil',
                'data': [chat.model_dump() for chat in chats_response]
            }), 200

        except ValidationError as pydantic_err:
            return jsonify({
                'success': False,
                'message': 'Validasi query parameter gagal',
                'errors': pydantic_err.errors(include_url=False)
            }), 422
        except Exception as e:
            logger.error(f"[CHAT CONTROLLER] Gagal mengambil daftar chat: {e}", exc_info=True)
            return jsonify({'success': False, 'message': 'Terjadi kesalahan pada server'})

    # ──────────────────────────────────────────────────────────────────────
    # GET /chats/<chat_id>
    # ──────────────────────────────────────────────────────────────────────
    @chat_controller.route('/chats/<string:chat_id>', methods=['GET'])
    @token_required
    def get_chat(chat_id: str):
        """
        Get chat detail
        ---
        tags:
          - Chat Session

        security:
          - Bearer: []

        parameters:
          - in: path
            name: chat_id
            type: string
            required: true

        responses:
          200:
            description: Chat detail retrieved successfully

          403:
            description: Forbidden - Bukan pemilik room chat

          404:
            description: Chat session tidak ditemukan
        """

        try:

            user_id_str = request.current_user.get("user_id")
            user_id = UUID(user_id_str)

            result = chat_service.get_chat(
                user_id=user_id,
                chat_id=chat_id
            )

            return jsonify({
                "success": True,
                "message": "Berhasil mengambil detail chat",
                "data": result.model_dump(mode="json")
            }), 200

        except ValueError as val_err:

            error_msg = str(val_err)

            if "Akses ditolak" in error_msg:
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 403

            return jsonify({
                "success": False,
                "message": error_msg
            }), 404

        except Exception as e:

            logger.error(
                f"[CHAT CONTROLLER] Gagal mengambil detail chat {chat_id}: {e}",
                exc_info=True
            )

            return jsonify({
                "success": False,
                "message": "Terjadi kesalahan pada server"
            }), 500

    return chat_controller