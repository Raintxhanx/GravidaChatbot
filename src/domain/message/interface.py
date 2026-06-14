from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from src.domain.message.model import (
    MessageResponseDTO, 
    MessageUpdateDTO,
    MessageGetAllDTO,
    MessageListResponseDTO
)

class IMessage(ABC):
    """Interface untuk pengelolaan pesan/messages di dalam chat room"""

    @abstractmethod
    def handle_user_message(self, chat_id: str, query: str, user_id_query: UUID) -> MessageResponseDTO: 
        """
        Alur Proses:
        1. Ambil 18 latest context + 1 first context dari DB.
        2. Format menjadi List[MessageContextDTO] -> Hit `query_retrieval_generator` -> Jadi `hidden_context`.
        3. Simpan pesan user baru (role='user', content=query, hidden_context=RAG_result) ke DB.
        4. Hit `chat_completion` menggunakan susunan: 18 latest + 1 first + pesan user baru tadi.
        5. Hasil response LLM disimpan ke DB sebagai pesan baru (role='assistant').
        6. Return MessageResponseDTO milik assistant ke frontend.
        """
        pass

    @abstractmethod
    def regenerate_last_message(self, chat_id: str, dto: MessageUpdateDTO, user_id_query: UUID) -> MessageResponseDTO:
        """
        Alur Proses:
        1. Hapus atau update pesan assistant terakhir (dan pesan user terkait jika query diubah).
        2. Panggil kembali `handle_user_message` dengan query yang sesuai.
        """
        pass

    @abstractmethod
    def get_all_message(self, chat_id: str, model: MessageGetAllDTO, user_id_query:UUID) -> MessageListResponseDTO:
        pass