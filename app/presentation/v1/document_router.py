from flask import Blueprint, request, jsonify
from functools import wraps
import jwt

def create_document_blueprint(rag_service, secret_key: str) -> Blueprint:
    """
    Factory function — menerima RAGApplicationService yang sudah di-inject dari luar.
    """
    doc_bp = Blueprint('document', __name__)

    # ──────────────────────────────────────────
    # Helper: JWT Auth Decorator
    # ──────────────────────────────────────────
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization', '')

            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

            if not token:
                return jsonify({'success': False, 'message': 'Token tidak ditemukan'}), 401

            try:
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                request.current_user = payload
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': 'Token sudah kadaluarsa'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': 'Token tidak valid'}), 401

            return f(*args, **kwargs)
        return decorated

    def admin_required(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user.get('role') != 'admin':
                return jsonify({'success': False, 'message': 'Akses ditolak: hanya admin'}), 403
            return f(*args, **kwargs)
        return decorated

    # ──────────────────────────────────────────
    # POST /documents/ingest
    # ──────────────────────────────────────────
    @doc_bp.route('/documents/ingest', methods=['POST'])
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
                text:
                  type: string
                  example: "Manfaat asam folat bagi ibu hamil adalah mencegah cacat tabung saraf."
                metadata:
                  type: object
                  example: {"source": "Buku Kesehatan A", "category": "Nutrisi"}
        responses:
          201:
            description: Document ingested successfully
          401:
            description: Unauthorized (Token missing or invalid)
          403:
            description: Forbidden (Admin role required)
          422:
            description: Unprocessable Entity (Validation error)
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        text = data.get('text', '').strip()
        metadata = data.get('metadata', {})

        if not text:
            return jsonify({'success': False, 'message': 'Field "text" wajib diisi'}), 422

        if not isinstance(metadata, dict):
            return jsonify({'success': False, 'message': 'Field "metadata" harus berupa objek'}), 422

        metadata['ingested_by'] = request.current_user.get('user_id')

        success, message = rag_service.ingest_document(text, metadata)
        if not success:
            return jsonify({'success': False, 'message': message}), 500

        return jsonify({'success': True, 'message': message}), 201

    # ──────────────────────────────────────────
    # POST /documents/ingest/batch
    # ──────────────────────────────────────────
    @doc_bp.route('/documents/ingest/batch', methods=['POST'])
    @admin_required
    def ingest_batch():
        """
        Batch Ingest Documents (Admin Only)
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
                documents:
                  type: array
                  items:
                    type: object
                    properties:
                      text:
                        type: string
                        example: "Data teks dokumen ke-1."
                      metadata:
                        type: object
                        example: {"source": "Batch Upload"}
        responses:
          200:
            description: Batch completed successfully
          207:
            description: Partial success (Some documents failed)
          401:
            description: Unauthorized
          422:
            description: Invalid array format
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        documents = data.get('documents', [])
        if not isinstance(documents, list) or len(documents) == 0:
            return jsonify({'success': False, 'message': 'Field "documents" harus berupa array dan tidak boleh kosong'}), 422

        # 1. Sisipkan 'ingested_by' ke dalam metadata masing-masing dokumen
        user_id = request.current_user.get('user_id')
        for doc in documents:
            if 'metadata' not in doc:
                doc['metadata'] = {}
            doc['metadata']['ingested_by'] = user_id

        # 2. Panggil fungsi Domain/Use Case yang sudah memiliki fitur Chunking
        result = rag_service.ingest_json_batch(documents)

        # 3. Format respons berdasarkan hasil dari Use Case
        is_partial_success = len(result['errors']) > 0
        status_code = 207 if is_partial_success else 200

        return jsonify({
            'success': True,
            'summary': {
                'total_documents_received': len(documents),
                'total_chunks_saved': result['total_chunks_saved'],
                'total_errors': len(result['errors']),
            },
            'status': result['status'],
            'errors': result['errors'] # Akan kosong jika sukses semua
        }), status_code

    @doc_bp.route('/documents/ingest-pdf', methods=['POST'])
    @admin_required
    def ingest_pdf_route():
        """
        Ingest PDF Document (Admin Only)
        ---
        tags:
          - Documents
        security:
          - Bearer: []
        consumes:
          - multipart/form-data
        parameters:
          - name: file
            in: formData
            type: file
            required: true
            description: File PDF yang akan diupload
          - name: source
            in: formData
            type: string
            required: false
            description: Sumber dokumen (opsional)
        responses:
          201:
            description: Document ingested successfully
          422:
            description: Unprocessable Entity (Bukan PDF)
          500:
            description: Internal Server Error
        """
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Tidak ada file yang diunggah'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nama file kosong'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'message': 'Hanya file PDF yang diizinkan'}), 422

        # Ambil metadata tambahan dari form-data jika ada
        metadata = {
            "filename": file.filename,
            "source": request.form.get("source", "Uploaded PDF"),
            "ingested_by": request.current_user.get('user_id')
        }

        # Baca file ke memory (stream) agar tidak perlu simpan di disk
        file_stream = file.read()
        
        success, message = rag_service.ingest_pdf(file_stream, metadata)
        
        if not success:
            return jsonify({'success': False, 'message': message}), 500

        return jsonify({'success': True, 'message': message}), 201

  # ──────────────────────────────────────────
    # POST /documents/retrieve (Bisa juga diletakkan di Chat Router)
    # ──────────────────────────────────────────
    @doc_bp.route('/documents/retrieve', methods=['POST'])
    @token_required # Biasanya user biasa boleh mengakses ini via chat
    def retrieve_documents():
        """
        Retrieve Context for LLM
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
                question:
                  type: string
                  example: "Apakah ISK berbahaya untuk janin?"
                top_k:
                  type: integer
                  default: 3
                  example: 3
        responses:
          200:
            description: Context retrieved successfully
          422:
            description: Question field is required
          500:
            description: Retrieval internal error
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'Body JSON tidak valid'}), 400

        question = data.get('question', '').strip()
        top_k = data.get('top_k', 3)

        if not question:
            return jsonify({'success': False, 'message': 'Field "question" wajib diisi'}), 422

        # Panggil Use Case
        result = rag_service.retrieve_context(question=question, top_k=top_k)

        if not result['success']:
            return jsonify(result), 500

        return jsonify({
            'success': True,
            'data': {
                'context_string': result['context'],
                'sources': result['raw_data']
            }
        }), 200

    # ──────────────────────────────────────────
    # GET /documents/health
    # ──────────────────────────────────────────
    @doc_bp.route('/documents/health', methods=['GET'])
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

    return doc_bp