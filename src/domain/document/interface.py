from abc import ABC, abstractmethod
from typing import Tuple, Any
from langchain_core.documents import Document

class IDocument(ABC):
    @abstractmethod
    def ingest_document(self, raw_doc: dict, metadata: dict) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def retrieve(self, query: str, metadata: dict | None = None) -> tuple[bool, Any]:
        pass