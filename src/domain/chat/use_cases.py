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

    def _retrieve_hits(self, query: str, source_label: str) -> List[dict]:
        """Melakukan retrieval ke Qdrant untuk satu query, lalu menandai asal sumbernya (user/model)."""
        success, hits = self._retrieval_service.retrieve(query=query)
        if success and isinstance(hits, list):
            for hit in hits:
                hit["asal_sumber"] = source_label
            return hits
        return []


    def _evaluate_best_retrieval(self, query: str, rag_result_query: str) -> tuple[str, str]:
        """
        Membandingkan hasil retrieval dari query user vs query hasil model,
        mengambil skor tertinggi di antara keduanya.

        - Jika skor tertinggi >= 0.85 -> pakai dokumen tsb, dan tentukan instruksi query
        berdasarkan asal sumber (model/user).
        - Jika tidak ada yang >= 0.85 -> tandai konteks tidak ditemukan.
        """
        hits_model = self._retrieve_hits(rag_result_query, "model")
        hits_user = self._retrieve_hits(query, "user")

        combined_hits = hits_model + hits_user

        best_score_result = None
        if combined_hits:
            best_score_result = max(combined_hits, key=lambda item: item["score"])

        retrieved_document = ""
        final_query_instruction = query  # default fallback kalau tidak ada hits sama sekali

        if best_score_result and best_score_result["score"] >= 0.10:
            retrieved_document = best_score_result["payload"].get("full_document_text", "")
            final_query_instruction = (
                rag_result_query if best_score_result["asal_sumber"] == "model" else query
            )
        else:
            retrieved_document = "#### KONTEKS TIDAK DITEMUKAN, JANGAN JAWAB PERTANYAAN USER"

        return retrieved_document, final_query_instruction

    # def create_new_chat_session(self, user_id: UUID, query: str) -> List[MessageResponseDTO]:
    #     logger.info(f"[CHAT SERVICE] Mencoba membuat sesi chat baru untuk User ID: {user_id}")
        
    #     try:
    #         # 1. Evaluasi Guardrail & Optimasi Query di Awal
    #         initial_context = [MessageContextDTO(role="user", content=query)]
    #         rag_result_query = self._chat_gen.query_retrieval_generator(initial_context)
            
    #         # 🔥 FIX BUG 1 & 2: Cegat langsung jika terdeteksi "abort" (off-context)
    #         if rag_result_query.strip().lower() == "abort":
    #             logger.warning(f"[GUARDRAIL] Deteksi prompt luar konteks saat membuat chat baru: '{query}'")
    #             raise ValueError("Maaf, saya hanya dapat membantu menjawab pertanyaan seputar kesehatan ibu hamil dan kehamilan.")

    #         # 2. Judul baru dibuat jika lolos guardrail
    #         generated_title = self._chat_gen.title_generation(query)
            
    #         # 🔥 FIX MASALAH 3: Gunakan full UUID demi keamanan jangka panjang
    #         chat_id = f"chat_{uuid.uuid4().hex.upper()}"
            
    #         # 3. Jalankan proses Retrieval ke Qdrant (Hanya jika lolos guardrail)
    #         logger.info(f"[CHAT SERVICE] Melakukan retrieval dengan query: {rag_result_query}")
    #         retrieval_success, hits = self._retrieval_service.retrieve(query=rag_result_query)
            
    #         retrieved_document = None
    #         if retrieval_success and hits:
    #             retrieved_document = hits[0]["payload"].get("full_document_text", "")
    #             logger.info(f"[CHAT SERVICE] Retrieval sukses. Score: {hits[0]['score']}")
    #         else:
    #             logger.warning("[CHAT SERVICE] Retrieval tidak mengembalikan hasil atau gagal.")

    #         hidden_context_payload = {
    #             "rag_query_instruction": rag_result_query,
    #             "retrieved_context": retrieved_document
    #         }

    #         # 4. Simpan info ChatRoom ke DB
    #         new_chat = ChatModel(
    #             id=chat_id,
    #             user_id=user_id,
    #             title=generated_title,
    #             description=None
    #         )
    #         self._db.add(new_chat)

    #         # 5. Buat Record Message 1: role='system'
    #         system_msg = MessageModel(
    #             id=f"{user_id}_{chat_id}_1",
    #             chat_id=chat_id,
    #             role="system",
    #             hidden_context=None,
    #             content=(
    #                 "You are a professional, empathetic, and reassuring doctor from Gravida. "
    #                 "You must always respond in polite, natural, and caring Indonesian. Provide accurate and factual medical answers. "
    #                 "If a context is included in the user's prompt, make sure to STRICTLY use only the facts from the context below to answer the question. "
    #                 "Do not hallucinate, guess, or make up any medical information. "
    #                 "If the context does not contain the answer, politely state that you cannot answer based on the provided information."
    #             )
    #         )
    #         self._db.add(system_msg)

    #         # 6. Buat Record Message 2: role='user'
    #         user_msg = MessageModel(
    #             id=f"{user_id}_{chat_id}_2",
    #             chat_id=chat_id,
    #             role="user",
    #             hidden_context=hidden_context_payload,
    #             content=query
    #         )
    #         self._db.add(user_msg)

    #         # 7. Pengayaan prompt dengan konteks medis untuk LLM Utama
    #         user_content_with_rag = query
    #         if retrieved_document:
    #             user_content_with_rag = (
    #                 f"### KONTEKS DOKUMEN MEDIS\n"
    #                 f"{retrieved_document}\n\n"
    #                 f"### INSTRUKSI TAMBAHAN\n"
    #                 f"Jawablah pertanyaan pasien di bawah dengan melakukan parafrase secara alami, "
    #                 f"sopan, dan penuh empati. Sampaikan informasi dengan bahasa Anda sendiri sebisa mungkin, "
    #                 f"tetapi JANGAN PERNAH menambahkan informasi medis, asumsi, atau diagnosis baru yang "
    #                 f"tidak tertulis di dalam teks konteks di atas.\n\n"
    #                 f"### PERTANYAAN PASIEN\n"
    #                 f"{query}"
    #             )

    #         history_for_llm = [
    #             MessageContextDTO(role=system_msg.role, content=system_msg.content),
    #             MessageContextDTO(role=user_msg.role, content=user_content_with_rag)
    #         ]

    #         # Panggil LLM utama
    #         llm_response_text = self._chat_gen.chat_completion(history_for_llm)

    #         # 8. Buat Record Message 3: role='assistant'
    #         assistant_msg = MessageModel(
    #             id=f"{user_id}_{chat_id}_3",
    #             chat_id=chat_id,
    #             role="assistant",
    #             hidden_context=None,
    #             content=llm_response_text
    #         )
    #         self._db.add(assistant_msg)

    #         # Commit seluruh rangkaian transaksi data ke DB secara atomik
    #         self._db.commit()
            
    #         logger.info(f"[CHAT SERVICE] Berhasil membuat Chat Room {chat_id} dengan RAG context.")
            
    #         return [
    #             MessageResponseDTO.model_validate(system_msg),
    #             MessageResponseDTO.model_validate(user_msg),
    #             MessageResponseDTO.model_validate(assistant_msg)
    #         ]

    #     except Exception as e:
    #         self._db.rollback()
    #         logger.error(f"[CHAT SERVICE] Gagal sistem saat membuat sesi chat baru: {e}", exc_info=True)
    #         raise e

    def prepare_chat_session(self, user_id: UUID, query: str) -> tuple[str, str, List[MessageContextDTO]]:
        """Tahap 1: Sinkronus - Melakukan guardrail, retrieval, dan simpan chat awal ke DB"""
        logger.info(f"[CHAT SERVICE] Mempersiapkan sesi chat baru untuk User ID: {user_id}")
        
        try:
            # 1. Evaluasi Guardrail
            initial_context = [MessageContextDTO(role="user", content=query)]
            
            # 🔥 PERBAIKAN DI SINI: Konsumsi generator menjadi string utuh
            rag_result_stream = self._chat_gen.query_retrieval_generator(initial_context)
            rag_result_query = "".join([token for token in rag_result_stream]).strip()
            
            # Sekarang Anda bisa melakukan pengecekan string dengan aman
            if rag_result_query.lower() == "abort":
                logger.warning(f"[GUARDRAIL] Deteksi prompt luar konteks: '{query}'")
                raise ValueError("Maaf, saya hanya dapat membantu menjawab pertanyaan seputar kesehatan ibu hamil dan kehamilan.")

            # 2. Judul & ID
            generated_title = self._chat_gen.title_generation(query)
            chat_id = f"chat_{uuid.uuid4().hex.upper()}"

            logger.info(f"[RAG SERVICE] Generated retrieval query: {rag_result_query}")
            
            # 3. Retrieval ke Qdrant + evaluasi skor tertinggi (user vs model query)
            retrieved_document, final_query_instruction = self._evaluate_best_retrieval(
                query=query,
                rag_result_query=rag_result_query
            )

            hidden_context_payload = {
                "rag_query_instruction": final_query_instruction,
                "retrieved_context": retrieved_document
            }

            # 4. Simpan info ChatRoom ke DB (Commit di awal agar ID valid terdaftar)
            new_chat = ChatModel(id=chat_id, user_id=user_id, title=generated_title, description=None)
            self._db.add(new_chat)

            # 5. Buat Record Message 1: system
            system_msg = MessageModel(
                id=f"{user_id}_{chat_id}_1", chat_id=chat_id, role="system", hidden_context=None,
                content="You are a professional, empathetic, and reassuring doctor from Gravida. You must always respond in polite, natural, and caring Indonesian. Provide accurate and factual medical answers. If a context is included in the user's prompt, make sure to STRICTLY use only the facts from the context below to answer the question. Do not hallucinate, guess, or make up any medical information. If the context does not contain the answer, politely state that you cannot answer based on the provided information."
            )
            self._db.add(system_msg)

            # 6. Buat Record Message 2: user
            user_msg = MessageModel(
                id=f"{user_id}_{chat_id}_2", chat_id=chat_id, role="user", hidden_context=hidden_context_payload, content=query
            )
            self._db.add(user_msg)

            # Commit tahap awal secara atomik, bebaskan koneksi DB sementara waktu
            self._db.commit()
            
            # 7. Pengayaan prompt RAG untuk LLM Utama
            user_content_with_rag = query
            if retrieved_document:
                user_content_with_rag = f"""
                    INSTRUKSI PENTING:
                    1. Jawab PERTANYAAN PASIEN hanya menggunakan fakta yang terdapat pada KONTEKS DOKUMEN MEDIS di bawah.
                    2. Jangan menambahkan informasi medis apa pun dari luar konteks.
                    3. Cukup parafrasekan informasi dari konteks dengan bahasa Indonesia yang sopan, natural, dan penuh kepedulian.

                    ### KONTEKS DOKUMEN MEDIS:
                    {retrieved_document}

                    ### PERTANYAAN PASIEN:
                    {query}
                """

            history_for_llm = [
                MessageContextDTO(role=system_msg.role, content=system_msg.content),
                MessageContextDTO(role=user_msg.role, content=user_content_with_rag)
            ]

            return chat_id, generated_title, history_for_llm

        except Exception as e:
            self._db.rollback()
            raise e


    def stream_llm_and_save_assistant(self, user_id: UUID, chat_id: str, history_for_llm: List[MessageContextDTO]):
        """Tahap 2: Streaming - Mengalirkan token LLM dan menyimpannya setelah selesai"""
        full_assistant_response = ""
        
        # Panggil generator stream dari Ollama Engine
        token_stream = self._chat_gen.chat_completion_stream(history_for_llm)
        
        for token in token_stream:
            full_assistant_response += token
            yield token  # Yield ke controller agar langsung diteruskan ke pasien
            
        # 8. Setelah streaming selesai secara utuh, simpan hasilnya ke DB (Transaksi Baru)
        if full_assistant_response:
            try:
                assistant_msg = MessageModel(
                    id=f"{user_id}_{chat_id}_3",
                    chat_id=chat_id,
                    role="assistant",
                    hidden_context=None,
                    content=full_assistant_response
                )
                self._db.add(assistant_msg)
                self._db.commit()
                logger.info(f"[CHAT SERVICE] Respon asisten berhasil disimpan ke DB untuk Chat ID: {chat_id}")
            except Exception as e:
                self._db.rollback()
                logger.error(f"[CHAT SERVICE] Gagal menyimpan potongan chat asisten ke DB: {e}")

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
        logger.info(f"[CHAT SERVICE] Mengonstruksi rangkuman untuk chat ID: {chat_id}")
        
        # 1. Ambil chat
        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        if not chat:
            raise ValueError("Chat session tidak ditemukan")

        # 2. Check ownership
        if chat.user_id != user_id:
            raise ValueError("Akses ditolak: Anda bukan pemilik room chat ini")

        try:
            # 3. Ambil messages khusus yang BUKAN 'system' prompt bawaan DB
            # Kita ingin murni mengambil percakapan user & assistant saja (Trim System Prompt)
            chat_messages = (
                self._db.query(MessageModel)
                .filter(
                    MessageModel.chat_id == chat_id,
                    MessageModel.role != "system"  # 🔥 KUNCI: Buang system prompt internal
                )
                .order_by(MessageModel.created_at.asc())
                .all()
            )
            
            if not chat_messages:
                raise ValueError("Chat room belum memiliki pesan user/assistant untuk dirangkum")

            # Strategi mengambil 20 pesan (pesan pertama user + 19 pesan terakhir)
            first_user_msg = chat_messages[0]
            remaining_msgs = chat_messages[1:]
            
            # Ambil maksimal 19 pesan terbaru dari sisa percakapan
            latest_msgs = remaining_msgs[-19:] if len(remaining_msgs) > 19 else remaining_msgs

            compiled = [first_user_msg] + latest_msgs
            
            # 4. Konversi ke DTO
            history_dto = [
                MessageContextDTO(role=msg.role, content=msg.content)
                for msg in compiled
            ]

            # 5. Hit Ollama & Konsumsi Stream (Karena .summarize() sekarang adalah generator)
            summary_stream = self._chat_gen.summarize(history_dto)
            summary_text = "".join([token for token in summary_stream]).strip()
            
            if not summary_text:
                raise ValueError("Ollama gagal menghasilkan rangkuman")

            # 6. Update DB
            chat.description = summary_text
            self._db.commit()
            self._db.refresh(chat)
            
            logger.info(f"[CHAT SERVICE] ✅ Summary created: {summary_text[:50]}...")
            return ChatResponseDTO.model_validate(chat)

        except Exception as e:
            self._db.rollback()
            logger.error(f"[CHAT SERVICE] ❌ Error: {e}", exc_info=True)
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