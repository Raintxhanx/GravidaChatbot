import logging
import json
from uuid import UUID
from typing import List, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, and_
from src.domain.message.interface import IMessage
from src.data.repo.chat_generation import ChatGeneration, MessageContextDTO

# Import DTOs
from src.domain.message.model import MessageListResponseDTO, MessageResponseDTO, MessageUpdateDTO, MessageGetAllDTO
from src.domain.document.interface import IDocument

# Import SQLAlchemy Models
from src.data.models.chats import ChatModel
from src.data.models.messages import MessageModel

logger = logging.getLogger(__name__)

class MessageUseCase(IMessage):
    """
    Implementation layer untuk manajemen pesan (Messages) di dalam chat room.
    Mengatur alur pengambilan konteks histori, RAG retrieval generator, 
    dan komunikasi dengan Ollama/LLM.
    """
    def __init__(self, db: Session, chat_gen_service: ChatGeneration, retrieval_service: IDocument):
        self._db = db
        self._chat_gen = chat_gen_service
        self._retrieval_service = retrieval_service # Tambahkan dependency retrieval service

    def handle_user_message(self, chat_id: str, query: str, user_id_query:UUID) -> MessageResponseDTO:
        logger.info(f"[MESSAGE SERVICE] Memproses pesan baru dari user di Chat ID: {chat_id}")
        
        # Validasi eksistensi chat room untuk mengambil user_id
        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        if not chat:
            logger.warning(f"[MESSAGE SERVICE] Sesi chat {chat_id} tidak ditemukan")
            raise ValueError("Chat session tidak ditemukan")
            
        user_id = chat.user_id

        if user_id != user_id_query:
            logger.warning(f"[SECURITY ALERT] User {user_id} mencoba merangkum chat room {chat_id} milik User {user_id_query}")
            raise ValueError({'success': False, 'message': 'Akses ditolak: Anda bukan pemilik room chat ini'})

        try:
            # 1. Ambil 1 first context (Pesan pertama / System Prompt)
            first_context = (
                self._db.query(MessageModel)
                .filter(MessageModel.chat_id == chat_id)
                .order_by(MessageModel.created_at.asc())
                .first()
            )
            
            # Ambil 18 latest context (Kecuali first_context)
            latest_contexts = []
            if first_context:
                latest_contexts = (
                    self._db.query(MessageModel)
                    .filter(MessageModel.chat_id == chat_id, MessageModel.id != first_context.id)
                    .order_by(MessageModel.created_at.desc())
                    .limit(18)
                    .all()
                )
                # Balikkan urutan dari DESC (kebutuhan query limit) ke ASC (kebutuhan urutan chat)
                latest_contexts.reverse()

            # Gabungkan menjadi susunan history: 1 first context + 18 latest context
            compiled_history = [first_context] + latest_contexts if first_context else latest_contexts

            # 2. Format menjadi List[MessageContextDTO]
            history_dtos = []
            for msg in compiled_history:
                if msg is None:
                    continue
                
                content_to_send = msg.content
                
                # Jika pesan history adalah dari user dan punya data RAG lama, gabungkan kembali
                if msg.role == "user" and msg.hidden_context:
                    # Memastikan hidden_context berbentuk dict (SQLAlchemy JSON type otomatis menjadi dict)
                    ctx_data = msg.hidden_context
                    if isinstance(ctx_data, str):
                        try:
                            ctx_data = json.loads(ctx_data)
                        except Exception:
                            ctx_data = {}
                    
                    old_document = ctx_data.get("retrieved_context")
                    if old_document:
                        content_to_send = (
                            f"Konteks Dokumen Medis:\n{old_document}\n\n"
                            f"Pertanyaan Pasien: {msg.content}"
                        )
                
                history_dtos.append(MessageContextDTO(role=msg.role, content=content_to_send))

            # Hit query_retrieval_generator untuk mendapatkan kata kunci optimasi RAG
            rag_result_query = self._chat_gen.query_retrieval_generator(history_dtos)
            
            # === PERBAIKAN RAG: Jalankan proses Retrieval ke Qdrant ===
            logger.info(f"[MESSAGE SERVICE] Melakukan retrieval dengan query hasil optimasi: {rag_result_query}")
            retrieval_success, hits = self._retrieval_service.retrieve(query=rag_result_query)
            
            retrieved_document = None
            if retrieval_success and hits:
                # Ambil dokumen dengan score tertinggi (index 0)
                retrieved_document = hits[0]["payload"].get("full_document_text", "")
                logger.info(f"[MESSAGE SERVICE] Retrieval sukses. Menemukan dokumen dengan score: {hits[0]['score']}")
            else:
                logger.warning("[MESSAGE SERVICE] Retrieval tidak menghasilkan dokumen atau gagal.")

            # Payload JSON untuk kolom hidden_context di database
            hidden_context_payload = {
                "rag_query_instruction": rag_result_query,
                "retrieved_context": retrieved_document
            }

            # Hitung jumlah pesan saat ini untuk menentukan increment custom ID berikutnya
            current_msg_count = self._db.query(MessageModel).filter(MessageModel.chat_id == chat_id).count()

            # 3. Simpan pesan user baru ke DB (Tetap simpan query murni dari user)
            user_msg_increment = current_msg_count + 1
            user_msg = MessageModel(
                id=f"{user_id}_{chat_id}_{user_msg_increment}",
                chat_id=chat_id,
                role="user",
                hidden_context=hidden_context_payload,
                content=query
            )
            self._db.add(user_msg)

            # 4. Ambil teks dokumen hasil retrieval, gabungkan ke pesan user saat dikirim ke LLM
            user_content_with_rag = query
            if retrieved_document:
                user_content_with_rag = (
                    f"Konteks Dokumen Medis:\n{retrieved_document}\n\n"
                    f"Pertanyaan Pasien: {query}"
                )

            # Hit chat_completion menggunakan susunan: history lama + pesan user kaya konteks RAG
            history_dtos.append(MessageContextDTO(role=user_msg.role, content=user_content_with_rag))
            llm_response_text = self._chat_gen.chat_completion(history_dtos)

            # 5. Hasil response LLM disimpan ke DB sebagai pesan baru (role='assistant')
            assistant_msg_increment = current_msg_count + 2
            assistant_msg = MessageModel(
                id=f"{user_id}_{chat_id}_{assistant_msg_increment}",
                chat_id=chat_id,
                role="assistant",
                hidden_context=None,
                content=llm_response_text
            )
            self._db.add(assistant_msg)

            # Commit seluruh rangkaian penambahan pesan
            self._db.commit()
            self._db.refresh(assistant_msg)

            logger.info(f"[MESSAGE SERVICE] Sukses menyimpan pesan user & assistant untuk Chat ID: {chat_id}")
            
            # 6. Return MessageResponseDTO milik assistant ke frontend
            return MessageResponseDTO.model_validate(assistant_msg)

        except Exception as e:
            self._db.rollback()
            logger.error(f"[MESSAGE SERVICE] Gagal sistem saat handle_user_message: {e}", exc_info=True)
            raise e

    def regenerate_last_message(self, chat_id: str, dto: MessageUpdateDTO, user_id_query:UUID) -> MessageResponseDTO:
        logger.info(f"[MESSAGE SERVICE] Meminta regenerasi pesan terakhir pada Chat ID: {chat_id}")

        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        user_id = chat.user_id

        if user_id != user_id_query:
            logger.warning(f"[SECURITY ALERT] User {user_id} mencoba merangkum chat room {chat_id} milik User {user_id_query}")
            raise ValueError({'success': False, 'message': 'Akses ditolak: Anda bukan pemilik room chat ini'})
        
        try:
            # 1. Ambil 2 pesan paling terakhir di DB (kronologis terbalik / DESC)
            # Urutkan berdasarkan created_at dan ID untuk menjamin pesan terbaru ada di atas
            last_two_messages = (
                self._db.query(MessageModel)
                .filter(MessageModel.chat_id == chat_id)
                .order_by(MessageModel.created_at.desc(), MessageModel.id.desc())
                .limit(2)
                .all()
            )

            if not last_two_messages:
                raise ValueError("Histori pesan kosong, tidak dapat melakukan regenerasi")

            # Hapus secara eksplisit tanpa peduli urutan indeks array
            for msg in last_two_messages:
                if msg.role in ["assistant", "user"]:
                    self._db.delete(msg)
            
            self._db.commit() # Pastikan benar-benar terhapus dari DB
            
            logger.info(f"[MESSAGE SERVICE] Konteks lama berhasil dibersihkan. Memicu ulang handle_user_message.")

            # 2. Panggil kembali handle_user_message (Otomatis menggunakan RAG baru)
            return self.handle_user_message(chat_id=chat_id, query=dto.query, user_id_query=user_id)

        except Exception as e:
            self._db.rollback()
            logger.error(f"[MESSAGE SERVICE] Gagal sistem saat melakukan regenerate_last_message: {e}", exc_info=True)
            raise e

    def get_all_message(
        self,
        chat_id: str,
        model: MessageGetAllDTO,
        user_id_query: UUID
    ) -> MessageListResponseDTO:

        logger.info(
            f"[MESSAGE SERVICE] Mengambil semua pesan untuk Chat ID: {chat_id}"
        )

        chat = (
            self._db.query(ChatModel)
            .filter(ChatModel.id == chat_id)
            .first()
        )

        if not chat:
            raise ValueError("Chat session tidak ditemukan")

        if chat.user_id != user_id_query:
            logger.warning(
                f"[SECURITY ALERT] User {user_id_query} mencoba mengakses histori chat room {chat_id}"
            )
            raise ValueError(
                "Akses ditolak: Anda bukan pemilik room chat ini"
            )

        try:
            query = (
                self._db.query(MessageModel)
                .filter(MessageModel.chat_id == chat_id)
            )

            # 1. Fitur Search (Sudah diperbaiki menggunakan cast ke String)
            # 1. Fitur Search (Fix Total untuk Kolom-Kolom Berjenis JSON)
            if model.search:
                search_pattern = f"%{model.search}%"

                query = query.filter(
                    or_(
                        # PERBAIKAN: Gunakan cast() untuk mengonversi keseluruhan kolom menjadi String
                        cast(MessageModel.content, String).ilike(search_pattern),
                        
                        # as_string() VALID di sini karena merujuk pada index expression ['kunci_json']
                        MessageModel.hidden_context['rag_query_instruction'].as_string().ilike(search_pattern),
                        
                        # as_string() VALID di sini
                        MessageModel.hidden_context['retrieved_context'].as_string().ilike(search_pattern)
                    )
                )

            # 2. Fitur Cursor Pagination (Telah Dikembalikan & Diperbaiki)
            if model.before_message_id:
                cursor_message = (
                    self._db.query(MessageModel)
                    .filter(
                        MessageModel.id == model.before_message_id,
                        MessageModel.chat_id == chat_id
                    )
                    .first()
                )

                if cursor_message:
                    query = query.filter(
                        or_(
                            MessageModel.created_at < cursor_message.created_at,
                            and_(
                                MessageModel.created_at == cursor_message.created_at,
                                MessageModel.id < cursor_message.id
                            )
                        )
                    )

            # Ambil 1 record ekstra untuk cek has_more
            messages = (
                query
                .order_by(
                    MessageModel.created_at.desc(),
                    MessageModel.id.desc()
                )
                .limit(model.limit + 1)
                .all()
            )

            has_more = len(messages) > model.limit

            if has_more:
                messages = messages[:model.limit]

            messages.reverse()

            items = [
                MessageResponseDTO.model_validate(msg)
                for msg in messages
            ]

            next_cursor = None

            if has_more and messages:
                # message tertua pada batch ini
                next_cursor = messages[0].id

            return MessageListResponseDTO(
                items=items,
                next_cursor=next_cursor,
                has_more=has_more
            )

        except Exception as e:
            logger.error(
                f"[MESSAGE SERVICE] Gagal sistem saat get_all_message: {e}",
                exc_info=True
            )
            raise