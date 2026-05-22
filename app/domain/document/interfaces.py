from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IVectorRepository(ABC):
    """Kontrak untuk interaksi dengan Vector Database"""
    @abstractmethod
    def save(self, vector: list[float], content: str, metadata: dict) -> None:
        pass

    @abstractmethod
    def search(self, query_vector: list[float], limit: int) -> list[dict]:
        pass

class IEmbeddingService(ABC):
    """Kontrak untuk transformasi teks menjadi vector"""
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        pass
    
    @abstractmethod
    def get_query_embedding(self, query: str) -> list[float]:
        pass

class ITextSplitter(ABC):
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        pass

class IDocumentParser(ABC):
    @abstractmethod
    def extract_text_from_pdf(self, file_stream) -> List[Dict[str, Any]]:
        """Mengembalikan list berisi dict per halaman: {'page_num': int, 'text': str}"""
        pass