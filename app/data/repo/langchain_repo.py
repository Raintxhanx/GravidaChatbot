from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.domain.document.interfaces import ITextSplitter

class LangChainTextSplitter(ITextSplitter):
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 250):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        )

    def split_text(self, text: str) -> List[str]:
        return self._splitter.split_text(text)