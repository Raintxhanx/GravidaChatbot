from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from src.domain.chat.model import (
    ChatResponseDTO, 
    ChatUpdateDTO,
    ChatGetAllDTO
)
from src.domain.message.model import MessageResponseDTO

class IChat(ABC):
    """Interface untuk manajemen sesi Chat (Akan melakukan hit DB langsung via SQLAlchemy Session)"""

    @abstractmethod
    def create_new_chat_session(self, user_id: UUID, query: str) -> List[MessageResponseDTO]: 
        """
        Alur Proses:
        1. Query masuk -> Hit `title_generation` -> Jadi Chat Title.
        2. Hit `query_retrieval_generator` -> Jadi `hidden_context` untuk pesan user.
        3. Buat 1 Record ChatRoom ke DB.
        4. Buat Record Message 1: role='system', hidden_context=None, content=pre-defined prompt.
        5. Buat Record Message 2: role='user', hidden_context=RAG_result, content=query.
        6. Hit chat_completion berdasarkan record 1 & 2. Hasilnya simpan ke DB sebagai record 3.
        7. Return ke-3 MessageResponseDTO tersebut ke frontend.
        """
        pass

    @abstractmethod
    def update_chat_session(self, chat_id: str, dto: ChatUpdateDTO, user_id:UUID) -> ChatResponseDTO:
        """Update standard properti chat (title / description)"""
        pass

    @abstractmethod
    def generate_chat_summary(self, chat_id: str, user_id:UUID) -> ChatResponseDTO:
        """
        Alur Proses:
        1. Ambil 19 latest context + 1 first context dari DB.
        2. Hit `summarize` pada ChatGenerationService.
        3. Update kolom description pada ChatModel di DB.
        """
        pass

    @abstractmethod
    def get_all_chat(self, user_id: UUID, dto: ChatGetAllDTO) -> List[ChatResponseDTO]:
        pass

    @abstractmethod
    def get_chat(self, user_id: UUID, chat_id: str) -> ChatResponseDTO:
        pass