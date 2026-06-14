import os
import logging
from flasgger import Swagger
from flask import Flask, jsonify
from dotenv import load_dotenv

from src.data.repo.qdrant import QdrantRepository
from src.data.repo.database import Database
from src.data.repo.chat_generation import ChatGeneration
from src.domain.chunker.use_cases import ChunkerUseCase
from src.domain.document.use_cases import DocumentUseCases
from src.domain.chat.use_cases import ChatUseCase
from src.domain.message.use_cases import MessageUseCase
from src.api.v1.document import create_document_blueprint
from src.api.v1.auth import create_auth_blueprint
from src.api.v1.collection import create_collection_blueprint
from src.api.v1.user import create_user_blueprint
from src.api.v1.chat import create_chat_blueprint
from src.api.v1.message import create_message_blueprint
from src.data.repo.bgem import BGELangChainEmbeddings, BGEM3Embedder
from src.domain.user.use_cases import UserUseCases
from src.domain.auth.use_cases import AuthUseCases
from src.util.password.hasher import PasswordHasher
from src.domain.collection.use_cases import CollectionUseCases

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, static_folder='dist', static_url_path='')

    load_dotenv()

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    QDRANT_URL= os.getenv("QDRANT_URL", "localhost")
    QDRANT_API_KEY=os.getenv("QDRANT_API_KEY", None)
    QDRANT_PORT=os.getenv("QDRANT_PORT", 443)
    API_KEY=os.getenv("API_KEY", "super-secret-key-change-me")
    ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "admin12345#")
    OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL", "localhost:11434")
    CF_CLIENT_ID=os.getenv("CF_CLIENT_ID", "none")
    CF_CLIENT_SECRET=os.getenv("CF_CLIENT_SECRET", "none")
    OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")

    # ── 1. Inisialisasi Swagger ──────────────────────────────────────────
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "RAG Application API",
            "description": "API Documentation for Retrieval-Augmented Generation App",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Format: Bearer <token>"
            },
            "ApiKey": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Format: ApiKey <secret_api_key>"
            }
        },
        "security": [
            {"Bearer": []},
            {"ApiKey": []}
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

    # ── 1. Embedder (shared, load sekali) ────────────────────────────────
    embedder = BGEM3Embedder(use_fp16=True, batch_size=12)
    lc_embeddings = BGELangChainEmbeddings(embedder=embedder)
    password_service = PasswordHasher()

    # ── 2. Repository ─────────────────────────────────────────────────────
    qdrant = QdrantRepository(
        url=QDRANT_URL,
        api_key= QDRANT_API_KEY,
        port=int(QDRANT_PORT),
    )

    chat_gen = ChatGeneration(cf_id=CF_CLIENT_ID,cf_secret=CF_CLIENT_SECRET,model_name=OLLAMA_MODEL,ollama_url=OLLAMA_BASE_URL)

    # ── Database ─────────────────────────────────────────────────────

    db = Database(DATABASE_URL)
    db.init_db()  # Generate tabel otomatis berdasarkan Base metadata

    # Amankan pengosongan session setelah populate admin selesai dijalankan
    startup_session = db.Session()
    try:
        db.populate_admin(
            db_session=startup_session, 
            password_service=password_service, 
            admin_password=ADMIN_PASSWORD
        )
    finally:
        db.Session.remove()

    # Manajemen penutupan session otomatis di akhir setiap HTTP Request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.Session.remove()

    # ── 3. Chunker (butuh lc_embeddings) ─────────────────────────────────
    chunker = ChunkerUseCase(
        lc_embeddings=lc_embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=85.0,
        min_chunk_size=100,
        max_chunk_size=2000,
    )

    # ── 4. Use Cases ──────────────────────────────────────────────────────
    collection_use_cases = CollectionUseCases(
        db=db.Session,
        qdrant_repo=qdrant,
    )

    document_use_cases = DocumentUseCases(
        collection_use_case=collection_use_cases,
        chunker=chunker,
        embedder=embedder,
        qdrant=qdrant,
    )

    user_use_cases = UserUseCases(
        db=db.Session,
        password_service=password_service,
    )

    auth_use_cases = AuthUseCases(
        db=db.Session,
        password_service=password_service,
    )

    chat_use_cases = ChatUseCase(
        db=db.Session,
        chat_gen_service=chat_gen,
        retrieval_service=document_use_cases,
    )

    message_use_cases = MessageUseCase(
        db=db.Session,
        chat_gen_service=chat_gen,
        retrieval_service=document_use_cases,
    )

    # ── 5. Inject & Register Blueprint ───────────────────────────────────

    API_PREFIX = "/api/v1"
    app.register_blueprint(
        create_document_blueprint(document_use_case=document_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),         
        url_prefix=API_PREFIX
    )

    # Register User Auth Blueprint
    app.register_blueprint(
        create_auth_blueprint(user_use_case=user_use_cases, auth_use_case=auth_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),
        url_prefix=API_PREFIX
    )

    app.register_blueprint(
        create_collection_blueprint(collection_use_case=collection_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),
        url_prefix=API_PREFIX
    )

    app.register_blueprint(
        create_chat_blueprint(chat_service=chat_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),
        url_prefix=API_PREFIX
    )

    app.register_blueprint(
        create_message_blueprint(message_service=message_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),
        url_prefix=API_PREFIX
    )

    app.register_blueprint(
        create_user_blueprint(user_service=user_use_cases, secret_key=SECRET_KEY, secret_api=API_KEY),
        url_prefix=API_PREFIX
    )

    # ── 6. Global Error Handlers ──────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        # Jika request mengarah ke API namun tidak ada, tetap return JSON 404
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "Endpoint tidak ditemukan"}), 404
        
        # Jika rute web biasa tidak ditemukan, arahkan balik ke index.html frontend (Sangat berguna untuk SPA routing)
        return app.send_static_file('index.html')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method tidak diizinkan"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "message": "Terjadi kesalahan internal server"}), 500

    # ── 7. Root Health Check ──────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"success": True, "message": "Server aktif dan berjalan"}), 200

    @app.route("/", methods=["GET"])
    def serve_frontend():
        return app.send_static_file("index.html")

    logger.info("App created")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)