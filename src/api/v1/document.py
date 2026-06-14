import logging
import jwt

from functools import wraps
from flask import Blueprint, jsonify, request
from src.domain.document.interface import IDocument
from src.util.middlewares.decorator_api import get_admin_required_decorator

logger = logging.getLogger(__name__)


def create_document_blueprint(document_use_case: IDocument, secret_api: str, secret_key: str) -> Blueprint:
    """
    Factory function — menerima RAGApplicationService yang sudah di-inject dari luar.
    """
    document_controller = Blueprint('document', __name__)
    admin_required = get_admin_required_decorator(secret_key, secret_api)

    # ──────────────────────────────────────────
    # POST /documents/ingest 
    # ──────────────────────────────────────────

    @document_controller.route("/documents/ingest", methods=["POST"])
    @admin_required
    def ingest_document():
        """
        Ingest Single Document (Admin Only)
        ---
        tags:
          - Documents
        security:
          - Bearer: []
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                raw_doc:
                  type: object
                  example: {"text": "Isi dokumen...", "topic": "Kesehatan"}
                metadata:
                  type: object
                  example: {"source": "Buku Kesehatan A", "category": "Nutrisi"}
        responses:
          201:
            description: Document ingested successfully
          422:
            description: Unprocessable Entity (Validation error)
          500:
            description: Internal Server Error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        raw_doc = data.get('raw_doc', {})
        metadata = data.get('metadata', {})

        if not raw_doc or not isinstance(raw_doc, dict):
            return jsonify({'success': False, 'message': 'Field "raw_doc" wajib diisi dan harus berupa objek'}), 422

        if not isinstance(metadata, dict):
            return jsonify({'success': False, 'message': 'Field "metadata" harus berupa objek'}), 422

        metadata['ingested_by'] = request.current_user.get('user_id')

        # Memanggil domain/use case logic Anda
        success, message = document_use_case.ingest_document(raw_doc=raw_doc, metadata=metadata)
        
        if not success:
            return jsonify({'success': False, 'message': message}), 500

        return jsonify({'success': True, 'message': message}), 201

    # ──────────────────────────────────────────
    # POST /documents/retrieve
    # ──────────────────────────────────────────
    
    @document_controller.route("/documents/retrieve", methods=["POST"])
    @admin_required
    def retrieve_documents():
        """
        Retrieve Context for LLM (Hybrid Search)
        ---
        tags:
          - Documents
        security:
          - Bearer: []
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                query:
                  type: string
                  example: "Apakah ISK berbahaya untuk janin?"
                limit:
                  type: integer
                  default: 3
                  example: 3
        responses:
          200:
            description: Context retrieved successfully
          422:
            description: Query field is required
          500:
            description: Retrieval internal error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        query = data.get('query', '').strip()
        limit = data.get('limit', 3)

        if not query:
            return jsonify({'success': False, 'message': 'Field "query" wajib diisi'}), 422

        # Gunakan metadata untuk membungkus parameter 'limit' agar sesuai dengan args retrieve() Anda
        retrieval_metadata = {"limit": limit}

        # Memanggil domain/use case logic Anda
        success, result = document_use_case.retrieve(query=query, metadata=retrieval_metadata)

        if not success:
            # Jika gagal, result berisi string error message dari Use Case
            return jsonify({'success': False, 'message': result}), 500

        # Jika sukses, result berisi formatted_hits
        return jsonify({
            'success': True,
            'data': result 
        }), 200
    
    # ──────────────────────────────────────────
    # GET /documents/health
    # ──────────────────────────────────────────
    
    @document_controller.route('/documents/health', methods=['GET'])
    def health_check():
        """
        Check Document Service Health
        ---
        tags:
          - Health
        responses:
          200:
            description: Service is healthy
        """
        return jsonify({
            'success': True,
            'message': 'Document service berjalan dengan baik',
        }), 200

    return document_controller