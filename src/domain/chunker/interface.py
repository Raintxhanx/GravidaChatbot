from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.documents import Document

class IChunker(ABC):
    @abstractmethod
    def chunk_document(self, raw_doc: Dict[str, Any], extra_metadata: Optional[Dict] = None) -> List[Document]:
        pass