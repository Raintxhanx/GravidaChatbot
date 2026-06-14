import hashlib
import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker

from src.domain.chunker.interface import IChunker
from src.data.repo.bgem import BGELangChainEmbeddings

logger = logging.getLogger(__name__)

class ChunkerUseCase(IChunker):
    def __init__(
        self,
        lc_embeddings: BGELangChainEmbeddings,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: float = 85.0,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self._splitter = SemanticChunker(
            embeddings=lc_embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount,
        )
        logger.info(
            f"SemanticChunker initialized — "
            f"strategy={breakpoint_threshold_type}@{breakpoint_threshold_amount}"
        )

    @staticmethod
    def _make_chunk_id(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def chunk_document(self, raw_doc: dict, extra_metadata: dict = None) -> list:
        formatted_text = MedicalQAFormatter.format(raw_doc)
        base_metadata = MedicalQAFormatter.extract_base_metadata(raw_doc, extra_metadata)

        if not formatted_text.strip():
            return []

        raw_chunks = self._splitter.create_documents([formatted_text])
        enriched_chunks = []

        # Simpan full_text di metadata — penting untuk RAG context recall
        full_text = raw_doc.get("text", "")

        for idx, chunk in enumerate(raw_chunks):
            chunk_text = chunk.page_content.strip()
            if len(chunk_text) < self.min_chunk_size:
                continue

            chunk_metadata = {
                **base_metadata,
                "chunk_index": idx,
                "chunk_total": len(raw_chunks),
                "chunk_size_chars": len(chunk_text),
                "chunk_id": self._make_chunk_id(chunk_text),
                # ⬇️ Ini kunci untuk RAG yang mengembalikan konteks penuh
                "full_document_text": full_text,
            }
            enriched_chunks.append(
                Document(page_content=chunk_text, metadata=chunk_metadata)
            )

        return enriched_chunks
    
class MedicalQAFormatter:
    @classmethod
    def format(cls, doc: dict) -> str:
        """
        Hasilkan teks yang context-aware untuk setiap chunk.
        Prefix topik + pertanyaan di-prepend agar setiap chunk
        hasil split tetap membawa konteks.
        """
        meta = doc.get("metadata", {})
        topic = meta.get("topic") or doc.get("topic", "")
        source_url = meta.get("source_url") or doc.get("url", "")
        text = doc.get("text", "").strip()

        if not text:
            return ""

        # Context anchor: selalu ada di awal, jadi SemanticChunker
        # akan membawa konteks ini ke setiap chunk via prefix
        header = f"[Topik]: {topic}\n" if topic else ""
        footer = f"\n\nSumber: {source_url}" if source_url else ""

        return f"{header}{text}{footer}"

    @classmethod
    def extract_base_metadata(cls, doc: dict, extra_metadata: dict = None) -> dict:
        meta = doc.get("metadata", {})
        
        # Ekstrak dari lokasi yang benar sesuai payload aktual
        topic = meta.get("topic") or doc.get("topic", "")
        url = meta.get("source_url") or doc.get("url", "")
        doc_id = meta.get("doc_id", "")

        base = {
            "topic": topic,
            "url": url,
            "doc_id": doc_id,
            "source_type": "medical_qa",
            "language": "id",
        }
        if extra_metadata:
            base.update(extra_metadata)
        return base