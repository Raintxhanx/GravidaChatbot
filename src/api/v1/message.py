import logging
import json
from uuid import UUID
from flask import Blueprint, request, jsonify, Response, stream_with_context
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.domain.message.interface import IMessage
from src.domain.message.model import MessageUpdateDTO, MessageGetAllDTO
from src.util.middlewares.decorator_api import get_token_required_decorator

logger = logging.getLogger(__name__)

def create_message_blueprint(message_service: IMessage, secret_key: str, secret_api: str) -> Blueprint:
    message_controller = Blueprint('message', __name__)
    token_required = get_token_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────────────────────────────────
    # POST /chats/<chat_id>/messages (Kirim Pesan Baru - STREAM)
    # ──────────────────────────────────────────────────────────────────────
    @message_controller.route('/chats/<string:chat_id>/messages', methods=['POST'])
    @token_required
    def send_message(chat_id: str):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        query = data.get('query', '').strip()
        if not query:
            return jsonify({'success': False, 'message': 'Parameter query wajib diisi'}), 422

        user_id_str = request.current_user.get('user_id')
        user_id = UUID(user_id_str)

        def generate_stream():
            try:
                # Panggil service layer yang sekarang menghasilkan Generator
                yield from message_service.handle_user_message(chat_id=chat_id, query=query, user_id_query=user_id)
            except Exception as e:
                logger.error(f"[MESSAGE CONTROLLER] Stream error: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': 'Terjadi kesalahan internal server'})}\n\n"

        return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

    # ──────────────────────────────────────────────────────────────────────
    # POST /chats/<chat_id>/messages/regenerate (Regenerasi Pesan Terakhir - STREAM)
    # ──────────────────────────────────────────────────────────────────────
    @message_controller.route('/chats/<string:chat_id>/messages/regenerate', methods=['POST'])
    @token_required
    def regenerate_message(chat_id: str):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        try:
            user_id_str = request.current_user.get('user_id')
            user_id = UUID(user_id_str)
            update_dto = MessageUpdateDTO(**data)

            def generate_stream():
                try:
                    yield from message_service.regenerate_last_message(chat_id=chat_id, dto=update_dto, user_id_query=user_id)
                except Exception as e:
                    logger.error(f"[MESSAGE CONTROLLER] Stream error regenerate: {e}", exc_info=True)
                    yield f"data: {json.dumps({'error': 'Terjadi kesalahan internal server'})}\n\n"

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

        except ValidationError as pydantic_err:
            return jsonify({
                'success': False, 
                'message': 'Validasi input gagal', 
                'errors': pydantic_err.errors(include_url=False)
            }), 422

    # ──────────────────────────────────────────────────────────────────────
    # GET /chats/<chat_id>/messages
    # ──────────────────────────────────────────────────────────────────────
    @message_controller.route('/chats/<string:chat_id>/messages', methods=['GET'])
    @token_required
    def get_messages(chat_id: str):
        """
        Get chat messages with cursor pagination
        ---
        tags:
          - Messages

        security:
          - Bearer: []

        parameters:
          - in: path
            name: chat_id
            type: string
            required: true

          - in: query
            name: search
            type: string
            required: false
            description: Kata kunci pencarian pada content atau hidden_context

          - in: query
            name: before_message_id
            type: string
            required: false
            description: Cursor untuk mengambil pesan yang lebih lama

          - in: query
            name: limit
            type: integer
            required: false
            default: 20

        responses:
          200:
            description: Messages retrieved successfully

          403:
            description: Forbidden - Bukan pemilik room chat

          404:
            description: Chat session tidak ditemukan

          422:
            description: Validation Error
        """

        search = request.args.get("search")
        before_message_id = request.args.get("before_message_id")
        limit = request.args.get("limit", 20, type=int)

        try:

            user_id_str = request.current_user.get("user_id")
            user_id = UUID(user_id_str)

            dto = MessageGetAllDTO(
                search=search,
                before_message_id=before_message_id,
                limit=limit
            )

            result = message_service.get_all_message(
                chat_id=chat_id,
                model=dto,
                user_id_query=user_id
            )

            return jsonify({
                "success": True,
                "message": "Berhasil mengambil histori pesan",
                "data": {
                    "items": [
                        item.model_dump(mode="json")
                        for item in result.items
                    ],
                    "next_cursor": result.next_cursor,
                    "has_more": result.has_more
                }
            }), 200

        except ValidationError as pydantic_err:

            return jsonify({
                "success": False,
                "message": "Validasi input gagal",
                "errors": pydantic_err.errors(include_url=False)
            }), 422

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
                f"[MESSAGE CONTROLLER] Gagal mengambil pesan pada chat {chat_id}: {e}",
                exc_info=True
            )

            return jsonify({
                "success": False,
                "message": "Terjadi kesalahan pada server"
            }), 500

    return message_controller