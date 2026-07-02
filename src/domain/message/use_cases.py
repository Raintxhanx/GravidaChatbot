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
            # 1. Ambil & Susun History (Konteks Mentah dari DB)
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

            # 2. Pembersihan Payload Histori untuk LLM & RAG Generator (Mencakup Trim System Prompt)
            rag_history_payload = []
            system_prompt_db = None  # Amankan system prompt asli DB untuk LLM utama nanti
            
            for dto in history_dtos:
                if dto.role == "system":
                    system_prompt_db = dto  # Simpan prompt internal Gravida
                    continue  # 🔥 TRIM: System prompt bawaan dikeluarkan agar tidak masuk ke payload RAG/Summarize
                
                content_str = str(dto.content)
                if dto.role == "user" and "Pertanyaan Pasien:" in content_str:
                    try:
                        content_str = content_str.split("Pertanyaan Pasien:")[-1].strip()
                    except Exception:
                        pass
                
                rag_history_payload.append(MessageContextDTO(role=dto.role, content=content_str))

            # Evaluasi Keyword via Guardrail LLM
            rag_evaluation_payload = rag_history_payload.copy()
            rag_evaluation_payload.append(MessageContextDTO(role="user", content=query))

            # 🔥 KUNCI UTAMA: Konsumsi generator token dari query_retrieval_generator menjadi satu string utuh
            rag_query_stream = self._chat_gen.query_retrieval_generator(rag_evaluation_payload)
            rag_result_query = "".join([token for token in rag_query_stream]).strip()
            
            # Guardrail Abort hanya dicek dari hasil LLM asli (bukan fallback)
            is_aborted = rag_result_query.lower() == "abort" if rag_result_query else False

            if not rag_result_query:
                logger.info(f"[MESSAGE SERVICE] RAG Generator blank. Fallback ke query user asli: '{query}'")

            # Eksekusi Pencarian ke Vector Database (Qdrant): user query vs model query
            retrieved_document = None
            final_query_instruction = rag_result_query

            if not is_aborted:
                search_query_for_model = rag_result_query if rag_result_query else query
                retrieved_document, final_query_instruction = self._evaluate_best_retrieval(
                    query=query,
                    rag_result_query=search_query_for_model
                )
                logger.info(f"[MESSAGE SERVICE] Final Retrieval instruction: {final_query_instruction}")

            # 3. Simpan Pesan User ke DB di awal
            current_msg_count = self._db.query(MessageModel).filter(MessageModel.chat_id == chat_id).count()
            user_msg_increment = current_msg_count + 1
            
            user_msg = MessageModel(
                id=f"{user_id}_{chat_id}_{user_msg_increment}",
                chat_id=chat_id,
                role="user",
                hidden_context={"rag_query_instruction": final_query_instruction, "retrieved_context": retrieved_document},
                content=query
            )
            self._db.add(user_msg)
            self._db.commit()

            # 4. Handle Guardrail (Abort)
            if is_aborted:
                logger.warning(f"[MESSAGE SERVICE] Guardrail aktif pada chat {chat_id}")
                abort_text = "Maaf, saya hanya dapat membantu pertanyaan yang berfokus pada medis dan kesehatan ibu hamil."
                yield f"data: {json.dumps({'token': abort_text})}\n\n"
                
                assistant_msg = MessageModel(
                    id=f"{user_id}_{chat_id}_{user_msg_increment + 1}", chat_id=chat_id,
                    role="assistant", hidden_context=None, content=abort_text
                )
                self._db.add(assistant_msg)
                self._db.commit()
                yield "data: [DONE]\n\n"
                return

            # 5. Konstruksi Payload Final khusus untuk LLM Utama (Stream)
            user_content_with_rag = query
            if retrieved_document:
                user_content_with_rag = f"""
                    INSTRUKSI PENTING:
                    1. Jawab PERTANYAAN PASIEN secara eksklusif dan KETAT hanya menggunakan fakta yang terdapat pada KONTEKS DOKUMEN MEDIS di bawah.
                    2. Jangan menebak, berhalusinasi, atau menambahkan informasi medis apa pun dari luar konteks.
                    3. Cukup parafrasekan informasi dari konteks dengan bahasa Indonesia yang sopan, natural, dan penuh kepedulian.
                    4. Jika konteks tidak menyediakan informasi yang cukup untuk menjawab, sampaikan permohonan maaf dengan sopan bahwa Anda tidak dapat menjawab berdasarkan informasi yang tersedia saat ini.

                    ### KONTEKS DOKUMEN MEDIS:
                    {retrieved_document}

                    ### PERTANYAAN PASIEN:
                    {query}
                """

            # Susun final payload dari data yang sudah di-strip bersih
            final_llm_payload = []
            if system_prompt_db:
                final_llm_payload.append(system_prompt_db)
                
            final_llm_payload.extend(rag_history_payload)
            final_llm_payload.append(MessageContextDTO(role=user_msg.role, content=user_content_with_rag))

            # 6. Jalankan Inference Stream
            full_response = ""
            for token in self._chat_gen.chat_completion_stream(final_llm_payload):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            # 7. Simpan Pesan Assistant setelah stream selesai secara utuh
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
        logger.info(f"[MESSAGE SERVICE] Meminta regenerasi/penyuntingan pesan pada Chat ID: {chat_id}")

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
            # 1. Ambil Histori Sesuai Pola Context (first_context + 17 message terakhir)
            first_context = self._db.query(MessageModel).filter(MessageModel.chat_id == chat_id).order_by(MessageModel.created_at.asc()).first()
            
            latest_contexts = []
            if first_context:
                latest_contexts = self._db.query(MessageModel).filter(
                    MessageModel.chat_id == chat_id, MessageModel.id != first_context.id
                ).order_by(MessageModel.created_at.desc()).limit(17).all()
                latest_contexts.reverse()

            compiled_history = [first_context] + latest_contexts if first_context else latest_contexts

            if not compiled_history:
                yield f"data: {json.dumps({'error': 'Histori kosong'})}\n\n"
                return

            # 2. Cari titik indeks awal mula penghapusan berdasarkan query
            target_index = None
            for i, msg in enumerate(compiled_history):
                if msg.role == "user" and msg.content == dto.query:
                    target_index = i
                    break

            # Fallback: Jika teks tidak cocok (berarti ini kasus menyunting/edit dengan query baru),
            # maka cari pesan 'user' paling terakhir sebagai jangkar regenerasi
            if target_index is None:
                for i in range(len(compiled_history) - 1, -1, -1):
                    if compiled_history[i] and compiled_history[i].role == "user":
                        target_index = i
                        break

            # 3. Hapus pesan dari indeks target tersebut sampai yang paling terakhir
            if target_index is not None:
                messages_to_delete = compiled_history[target_index:]
                for msg in messages_to_delete:
                    if msg and msg.role in ["user", "assistant"]:
                        self._db.delete(msg)
                
                self._db.commit()
                logger.info(f"[MESSAGE SERVICE] Konteks lama dibersihkan dari DB (Index {target_index} s/d terakhir).")
            else:
                logger.warning(f"[MESSAGE SERVICE] Tidak menemukan jangkar pesan user untuk diregenerasi.")

            # 4. Limpahkan langsung ke fungsi stream utama dengan query yang baru/lama
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