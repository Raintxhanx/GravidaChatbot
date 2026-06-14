import logging
import uuid
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String

# Import Interfaces & Services
from src.domain.chat.interface import IChat
from src.data.repo.chat_generation import ChatGeneration, MessageContextDTO

# Import DTOs (Sesuai dengan blueprint path Anda)
from src.domain.chat.model import ChatResponseDTO, ChatUpdateDTO, ChatGetAllDTO
from src.domain.message.model import MessageResponseDTO
from src.domain.document.interface import IDocument

# Import SQLAlchemy Models
from src.data.models.chats import ChatModel
from src.data.models.messages import MessageModel

logger = logging.getLogger(__name__)

class ChatUseCase(IChat):
    """
    Implementation layer untuk manajemen sesi Chat dan orkestrasi 
    LLM Chat Generation dengan database PostgreSQL via SQLAlchemy.
    """
    def __init__(self, db: Session, chat_gen_service: ChatGeneration, retrieval_service: IDocument):
        self._db = db
        self._chat_gen = chat_gen_service
        self._retrieval_service = retrieval_service


    def create_new_chat_session(self, user_id: UUID, query: str) -> List[MessageResponseDTO]:
        logger.info(f"[CHAT SERVICE] Mencoba membuat sesi chat baru untuk User ID: {user_id}")
        
        try:
            # 1. Evaluasi Guardrail & Optimasi Query di Awal
            initial_context = [MessageContextDTO(role="user", content=query)]
            rag_result_query = self._chat_gen.query_retrieval_generator(initial_context)
            
            # 🔥 FIX BUG 1 & 2: Cegat langsung jika terdeteksi "abort" (off-context)
            if rag_result_query.strip().lower() == "abort":
                logger.warning(f"[GUARDRAIL] Deteksi prompt luar konteks saat membuat chat baru: '{query}'")
                raise ValueError("Maaf, saya hanya dapat membantu menjawab pertanyaan seputar kesehatan ibu hamil dan kehamilan.")

            # 2. Judul baru dibuat jika lolos guardrail
            generated_title = self._chat_gen.title_generation(query)
            
            # 🔥 FIX MASALAH 3: Gunakan full UUID demi keamanan jangka panjang
            chat_id = f"chat_{uuid.uuid4().hex.upper()}"
            
            # 3. Jalankan proses Retrieval ke Qdrant (Hanya jika lolos guardrail)
            logger.info(f"[CHAT SERVICE] Melakukan retrieval dengan query: {rag_result_query}")
            retrieval_success, hits = self._retrieval_service.retrieve(query=rag_result_query)
            
            retrieved_document = None
            if retrieval_success and hits:
                retrieved_document = hits[0]["payload"].get("full_document_text", "")
                logger.info(f"[CHAT SERVICE] Retrieval sukses. Score: {hits[0]['score']}")
            else:
                logger.warning("[CHAT SERVICE] Retrieval tidak mengembalikan hasil atau gagal.")

            hidden_context_payload = {
                "rag_query_instruction": rag_result_query,
                "retrieved_context": retrieved_document
            }

            # 4. Simpan info ChatRoom ke DB
            new_chat = ChatModel(
                id=chat_id,
                user_id=user_id,
                title=generated_title,
                description=None
            )
            self._db.add(new_chat)

            # 5. Buat Record Message 1: role='system'
            system_msg = MessageModel(
                id=f"{user_id}_{chat_id}_1",
                chat_id=chat_id,
                role="system",
                hidden_context=None,
                content=(
                    "You are a professional, empathetic, and reassuring doctor from Gravida. "
                    "You must always respond in polite, natural, and caring Indonesian. Provide accurate and factual medical answers. "
                    "If a context is included in the user's prompt, make sure to STRICTLY use only the facts from the context below to answer the question. "
                    "Do not hallucinate, guess, or make up any medical information. "
                    "If the context does not contain the answer, politely state that you cannot answer based on the provided information."
                )
            )
            self._db.add(system_msg)

            # 6. Buat Record Message 2: role='user'
            user_msg = MessageModel(
                id=f"{user_id}_{chat_id}_2",
                chat_id=chat_id,
                role="user",
                hidden_context=hidden_context_payload,
                content=query
            )
            self._db.add(user_msg)

            # 7. Pengayaan prompt dengan konteks medis untuk LLM Utama
            user_content_with_rag = query
            if retrieved_document:
                user_content_with_rag = (
                    f"### KONTEKS DOKUMEN MEDIS\n"
                    f"{retrieved_document}\n\n"
                    f"### INSTRUKSI TAMBAHAN\n"
                    f"Jawablah pertanyaan pasien di bawah dengan melakukan parafrase secara alami, "
                    f"sopan, dan penuh empati. Sampaikan informasi dengan bahasa Anda sendiri sebisa mungkin, "
                    f"tetapi JANGAN PERNAH menambahkan informasi medis, asumsi, atau diagnosis baru yang "
                    f"tidak tertulis di dalam teks konteks di atas.\n\n"
                    f"### PERTANYAAN PASIEN\n"
                    f"{query}"
                )

            history_for_llm = [
                MessageContextDTO(role=system_msg.role, content=system_msg.content),
                MessageContextDTO(role=user_msg.role, content=user_content_with_rag)
            ]

            # Panggil LLM utama
            llm_response_text = self._chat_gen.chat_completion(history_for_llm)

            # 8. Buat Record Message 3: role='assistant'
            assistant_msg = MessageModel(
                id=f"{user_id}_{chat_id}_3",
                chat_id=chat_id,
                role="assistant",
                hidden_context=None,
                content=llm_response_text
            )
            self._db.add(assistant_msg)

            # Commit seluruh rangkaian transaksi data ke DB secara atomik
            self._db.commit()
            
            logger.info(f"[CHAT SERVICE] Berhasil membuat Chat Room {chat_id} dengan RAG context.")
            
            return [
                MessageResponseDTO.model_validate(system_msg),
                MessageResponseDTO.model_validate(user_msg),
                MessageResponseDTO.model_validate(assistant_msg)
            ]

        except Exception as e:
            self._db.rollback()
            logger.error(f"[CHAT SERVICE] Gagal sistem saat membuat sesi chat baru: {e}", exc_info=True)
            raise e

    
    def update_chat_session(self, chat_id: str, dto: ChatUpdateDTO, user_id:UUID) -> ChatResponseDTO:
        logger.info(f"[CHAT SERVICE] Memperbarui properti room chat ID: {chat_id}")
        
        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        if not chat:
            logger.warning(f"[CHAT SERVICE] Gagal memperbarui: Chat Room {chat_id} tidak ditemukan")
            raise ValueError("Chat session tidak ditemukan")
        
        chat_user_id = chat.user_id

        if chat_user_id != user_id:
            logger.warning(f"[SECURITY ALERT] User {chat_user_id} mencoba merangkum chat room {chat_id} milik User {user_id}")
            raise ValueError({'success': False, 'message': 'Akses ditolak: Anda bukan pemilik room chat ini'})

        try:
            update_data = dto.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(chat, key, value)
                
            self._db.commit()
            self._db.refresh(chat)
            
            return ChatResponseDTO.model_validate(chat)
            
        except Exception as e:
            self._db.rollback()
            logger.error(f"[CHAT SERVICE] Gagal sistem saat memperbarui chat {chat_id}: {e}", exc_info=True)
            raise e

    def generate_chat_summary(self, chat_id: str, user_id: UUID) -> ChatResponseDTO:
        logger.info(f"[CHAT SERVICE] Mengonstruksi rangkuman otomatis untuk chat ID: {chat_id}")
        
        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        if not chat:
            logger.warning(f"[CHAT SERVICE] Gagal merangkum: Chat Room {chat_id} tidak ditemukan")
            raise ValueError("Chat session tidak ditemukan")

        chat_user_id = chat.user_id

        if chat_user_id != user_id:
            logger.warning(f"[SECURITY ALERT] User {chat_user_id} mencoba merangkum chat room {chat_id} milik User {user_id}")
            raise ValueError({'success': False, 'message': 'Akses ditolak: Anda bukan pemilik room chat ini'})

        try:
            # 1. Ambil 1 first context (Pesan pertama / System Prompt biasanya)
            first_context = (
                self._db.query(MessageModel)
                .filter(MessageModel.chat_id == chat_id)
                .order_by(MessageModel.created_at.asc())
                .first()
            )
            
            if not first_context:
                raise ValueError("Tidak ada pesan di dalam room chat ini untuk dirangkum")

            # Ambil 19 latest context (Kecuali first_context agar tidak ganda jika pesan masih sedikit)
            latest_contexts = (
                self._db.query(MessageModel)
                .filter(MessageModel.chat_id == chat_id, MessageModel.id != first_context.id)
                .order_by(MessageModel.created_at.desc())
                .limit(19)
                .all()
            )
            # Balikkan urutan latest context dari desc (DB query) ke asc (urutan kronologis chat)
            latest_contexts.reverse()

            # Gabungkan 1 first context + 19 latest context
            compiled_messages = [first_context] + latest_contexts
            
            # Format ke List[MessageContextDTO]
            history_dto = [
                MessageContextDTO(role=msg.role, content=msg.content) 
                for msg in compiled_messages
            ]

            # 2. Hit summarize pada ChatGenerationService
            summary_result = self._chat_gen.summarize(history_dto)

            # 3. Update kolom description pada ChatModel di DB
            chat.description = summary_result
            
            self._db.commit()
            self._db.refresh(chat)
            
            logger.info(f"[CHAT SERVICE] Kolom deskripsi chat {chat_id} berhasil di-update dengan rangkuman baru.")
            return ChatResponseDTO.model_validate(chat)

        except Exception as e:
            self._db.rollback()
            logger.error(f"[CHAT SERVICE] Gagal sistem saat menghasilkan rangkuman chat {chat_id}: {e}", exc_info=True)
            raise e

    def get_all_chat(self, user_id: UUID, model: ChatGetAllDTO) -> List[ChatResponseDTO]:
        logger.info(f"[CHAT SERVICE] Mengambil semua sesi chat untuk User ID: {user_id}")
        
        try:
            # Base query: Proteksi layer agar user hanya bisa melihat chat miliknya sendiri
            query = self._db.query(ChatModel).filter(ChatModel.user_id == user_id)

            # Fitur Pencarian pada kolom 'title' DAN 'description'
            if model.search:
                search_pattern = f"%{model.search}%"
                query = query.filter(
                    or_(
                        ChatModel.title.ilike(search_pattern),
                        ChatModel.description.ilike(search_pattern)
                    )
                )

            # Filter tambahan berdasarkan range tanggal (jika dikirim oleh frontend)
            if model.start_date:
                query = query.filter(ChatModel.created_at >= model.start_date)
            if model.end_date:
                query = query.filter(ChatModel.created_at <= model.end_date)

            # Urutan dari terlama ke terbaru (ASC) beserta Pagination
            chats = (
                query.order_by(ChatModel.created_at.asc())
                .offset(model.skip)
                .limit(model.limit)
                .all()
            )

            # Transformasikan hasil ke bentuk List[ChatResponseDTO]
            return [ChatResponseDTO.model_validate(chat) for chat in chats]

        except Exception as e:
            logger.error(f"[CHAT SERVICE] Gagal sistem saat get_all chat: {e}", exc_info=True)
            raise e

    def get_chat(self, user_id: UUID, chat_id: str) -> ChatResponseDTO:
        logger.info(
            f"[CHAT SERVICE] Mengambil detail chat ID: {chat_id} untuk User ID: {user_id}"
        )

        try:
            chat = (
                self._db.query(ChatModel)
                .filter(ChatModel.id == chat_id)
                .first()
            )

            if not chat:
                logger.warning(
                    f"[CHAT SERVICE] Chat Room {chat_id} tidak ditemukan"
                )
                raise ValueError("Chat session tidak ditemukan")

            if chat.user_id != user_id:
                logger.warning(
                    f"[SECURITY ALERT] User {user_id} mencoba mengakses chat {chat_id} milik User {chat.user_id}"
                )
                raise ValueError(
                    "Akses ditolak: Anda bukan pemilik room chat ini"
                )

            return ChatResponseDTO.model_validate(chat)

        except Exception as e:
            logger.error(
                f"[CHAT SERVICE] Gagal mengambil detail chat {chat_id}: {e}",
                exc_info=True
            )
            raise e