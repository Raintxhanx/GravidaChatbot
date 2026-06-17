import json
import logging
from uuid import UUID
from typing import List, Generator
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, and_

from src.domain.message.interface import IMessage
from src.data.repo.chat_generation import ChatGeneration, MessageContextDTO
from src.domain.message.model import MessageListResponseDTO, MessageResponseDTO, MessageUpdateDTO, MessageGetAllDTO
from src.domain.document.interface import IDocument
from src.data.models.chats import ChatModel
from src.data.models.messages import MessageModel

logger = logging.getLogger(__name__)

class MessageUseCase(IMessage):
    def __init__(self, db: Session, chat_gen_service: ChatGeneration, retrieval_service: IDocument):
        self._db = db
        self._chat_gen = chat_gen_service
        self._retrieval_service = retrieval_service

    def handle_user_message(self, chat_id: str, query: str, user_id_query: UUID) -> Generator[str, None, None]:
        logger.info(f"[MESSAGE SERVICE] Memproses pesan stream baru dari user di Chat ID: {chat_id}")
        
        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        if not chat:
            logger.warning(f"[MESSAGE SERVICE] Sesi chat {chat_id} tidak ditemukan")
            yield f"data: {json.dumps({'error': 'Chat session tidak ditemukan'})}\n\n"
            return
            
        user_id = chat.user_id
        if user_id != user_id_query:
            logger.warning(f"[SECURITY ALERT] User {user_id_query} mencoba akses room {chat_id}")
            yield f"data: {json.dumps({'error': 'Akses ditolak'})}\n\n"
            return

        try:
            # 1. Ambil & Susun History
            first_context = self._db.query(MessageModel).filter(MessageModel.chat_id == chat_id).order_by(MessageModel.created_at.asc()).first()
            
            latest_contexts = []
            if first_context:
                latest_contexts = self._db.query(MessageModel).filter(
                    MessageModel.chat_id == chat_id, MessageModel.id != first_context.id
                ).order_by(MessageModel.created_at.desc()).limit(18).all()
                latest_contexts.reverse()

            compiled_history = [first_context] + latest_contexts if first_context else latest_contexts

            history_dtos = []
            for msg in compiled_history:
                if msg is None: continue
                content_to_send = msg.content
                if msg.role == "user" and msg.hidden_context:
                    ctx_data = msg.hidden_context if isinstance(msg.hidden_context, dict) else (json.loads(msg.hidden_context) if isinstance(msg.hidden_context, str) else {})
                    old_document = ctx_data.get("retrieved_context")
                    if old_document:
                        content_to_send = f"Konteks Dokumen Medis:\n{old_document}\n\nPertanyaan Pasien: {msg.content}"
                history_dtos.append(MessageContextDTO(role=msg.role, content=content_to_send))

            # 2. RAG Generator & Guardrail Check
            rag_result_query = self._chat_gen.query_retrieval_generator(history_dtos)
            is_aborted = rag_result_query.strip().lower() == "abort"
            
            retrieved_document = None
            if not is_aborted:
                logger.info(f"[MESSAGE SERVICE] Retrieval query: {rag_result_query}")
                retrieval_success, hits = self._retrieval_service.retrieve(query=rag_result_query)
                if retrieval_success and hits:
                    retrieved_document = hits[0]["payload"].get("full_document_text", "")

            # 3. Simpan Pesan User ke DB di awal
            current_msg_count = self._db.query(MessageModel).filter(MessageModel.chat_id == chat_id).count()
            user_msg_increment = current_msg_count + 1
            
            user_msg = MessageModel(
                id=f"{user_id}_{chat_id}_{user_msg_increment}",
                chat_id=chat_id,
                role="user",
                hidden_context={"rag_query_instruction": rag_result_query, "retrieved_context": retrieved_document},
                content=query
            )
            self._db.add(user_msg)
            self._db.commit()

            # 4. Handle Guardrail (Abort)
            if is_aborted:
                logger.warning(f"[MESSAGE SERVICE] Guardrail aktif pada chat {chat_id}")
                abort_text = "Maaf, saya hanya dapat membantu pertanyaan yang berfokus pada medis dan kesehatan ibu hamil."
                yield f"data: {json.dumps({'token': abort_text})}\n\n"
                
                # Simpan balasan abort sebagai assistant
                assistant_msg = MessageModel(
                    id=f"{user_id}_{chat_id}_{user_msg_increment + 1}", chat_id=chat_id,
                    role="assistant", hidden_context=None, content=abort_text
                )
                self._db.add(assistant_msg)
                self._db.commit()
                yield "data: [DONE]\n\n"
                return

            # 5. Gabungkan konteks dan kirim ke LLM Stream
            user_content_with_rag = query
            if retrieved_document:
                user_content_with_rag = f"Konteks Dokumen Medis:\n{retrieved_document}\n\nPertanyaan Pasien: {query}"

            history_dtos.append(MessageContextDTO(role=user_msg.role, content=user_content_with_rag))

            full_response = ""
            for token in self._chat_gen.chat_completion_stream(history_dtos):
                full_response += token
                # Yield data dengan format Server-Sent Events (SSE)
                yield f"data: {json.dumps({'token': token})}\n\n"

            # 6. Simpan Pesan Assistant setelah stream selesai
            if full_response:
                assistant_msg = MessageModel(
                    id=f"{user_id}_{chat_id}_{user_msg_increment + 1}",
                    chat_id=chat_id,
                    role="assistant",
                    hidden_context=None,
                    content=full_response
                )
                self._db.add(assistant_msg)
                self._db.commit()

            yield "data: [DONE]\n\n"

        except Exception as e:
            self._db.rollback()
            logger.error(f"[MESSAGE SERVICE] Gagal handle_user_message: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    def regenerate_last_message(self, chat_id: str, dto: MessageUpdateDTO, user_id_query: UUID) -> Generator[str, None, None]:
        logger.info(f"[MESSAGE SERVICE] Meminta regenerasi pesan pada Chat ID: {chat_id}")

        chat = self._db.query(ChatModel).filter(ChatModel.id == chat_id).first()
        user_id = chat.user_id

        if user_id != user_id_query:
            logger.warning(f"[SECURITY ALERT] User {user_id_query} mencoba akses room {chat_id}")
            yield f"data: {json.dumps({'error': 'Akses ditolak'})}\n\n"
            return
        
        try:
            last_two_messages = self._db.query(MessageModel).filter(
                MessageModel.chat_id == chat_id
            ).order_by(MessageModel.created_at.desc(), MessageModel.id.desc()).limit(2).all()

            if not last_two_messages:
                yield f"data: {json.dumps({'error': 'Histori kosong'})}\n\n"
                return

            for msg in last_two_messages:
                if msg.role in ["assistant", "user"]:
                    self._db.delete(msg)
            
            self._db.commit()
            logger.info(f"[MESSAGE SERVICE] Konteks dibersihkan. Memicu ulang stream.")

            # Limpahkan langsung ke fungsi stream utama
            yield from self.handle_user_message(chat_id=chat_id, query=dto.query, user_id_query=user_id)

        except Exception as e:
            self._db.rollback()
            logger.error(f"[MESSAGE SERVICE] Gagal regenerate: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

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