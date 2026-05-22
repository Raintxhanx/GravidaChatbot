import os
from flask import Flask, jsonify
from flasgger import Swagger

from app.data.models.user import db
from app.data.repo.langchain_repo import LangChainTextSplitter
from app.data.repo.pdf_repo import PyMuPDFParser
from app.data.repo.postgresql_repo import SQLUserRepository
from app.data.repo.qdrant_repo import get_qdrant_client, QdrantRepository
from app.data.repo.sentence_transformers import SentenceTransformerImpl
from app.domain.document.use_cases import RAGApplicationService
from app.domain.user.use_cases import UserUseCase
from app.presentation.v1.user_router import create_user_blueprint
from app.presentation.v1.document_router import create_document_blueprint


def create_app() -> Flask:
    app = Flask(__name__)

    # ──────────────────────────────────────────
    # 1. Konfigurasi Aplikasi
    # ──────────────────────────────────────────
    app.config['SECRET_KEY']            = os.getenv('SECRET_KEY', 'dev-secret-ganti-di-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://ajiandrain:RaihanSecret1309@localhost:5433/pregnancy_guide'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Hapus app.config['SWAGGER'] yang lama, ganti dengan ini:
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Pregnancy Guide API",
            "description": "API Documentation for Pregnancy Guide App",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Format: Bearer <token>"
            }
        },
        "security": [
            {"Bearer": []}
        ]
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    Swagger(app, template=swagger_template, config=swagger_config)

    # ──────────────────────────────────────────
    # 2. Inisialisasi Database (SQLAlchemy)
    # ──────────────────────────────────────────
    db.init_app(app)

    with app.app_context():
        db.create_all()   # Buat tabel jika belum ada

    # ──────────────────────────────────────────
    # 3. Inisialisasi Infrastruktur Vector DB
    # ──────────────────────────────────────────
    qdrant_client = get_qdrant_client()
    vector_repo   = QdrantRepository(
        client=qdrant_client,
        collection_name=os.getenv('QDRANT_COLLECTION', 'alodokter_collection_v2')
    )

    # ──────────────────────────────────────────
    # 4. Inisialisasi ML Service (Embedder)
    # ──────────────────────────────────────────

    embedder = SentenceTransformerImpl(
        os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-small')
    )

    # ──────────────────────────────────────────
    # 5. Inisialisasi Langchain (Text Splitter)
    # ──────────────────────────────────────────

    langchain = LangChainTextSplitter(chunk_size=700, chunk_overlap=150)
    doc_parser = PyMuPDFParser()  # Parser PDF menggunakan PyMuPDF

    # ──────────────────────────────────────────
    # 6. Inisialisasi Repository & Use Case
    # ──────────────────────────────────────────
    user_repo     = SQLUserRepository()
    secret_key    = app.config['SECRET_KEY']

    rag_service   = RAGApplicationService(vector_repo, embedder, langchain, doc_parser)
    user_use_case = UserUseCase(repo=user_repo, secret_key=secret_key)

    # ──────────────────────────────────────────
    # 7. Registrasi Blueprint (Routing Layer)
    # ──────────────────────────────────────────
    API_PREFIX = '/api/v1'

    app.register_blueprint(
        create_user_blueprint(user_use_case, secret_key),
        url_prefix=API_PREFIX
    )
    app.register_blueprint(
        create_document_blueprint(rag_service, secret_key),
        url_prefix=API_PREFIX
    )

    # ──────────────────────────────────────────
    # 8. Global Error Handlers
    # ──────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Endpoint tidak ditemukan'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'message': 'Method tidak diizinkan'}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'success': False, 'message': 'Terjadi kesalahan internal server'}), 500

    # ──────────────────────────────────────────
    # 9. Root Health Check
    # ──────────────────────────────────────────
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'success': True, 'message': 'Server aktif dan berjalan'}), 200

    return app  