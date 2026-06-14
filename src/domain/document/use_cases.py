import logging
import json
from typing import Tuple, Any

from src.domain.collection.interface import ICollection
from src.data.repo.qdrant import QdrantRepository
from src.domain.chunker.interface import IChunker
from src.domain.document.interface import IDocument
from src.data.repo.bgem import BGEM3Embedder

logger = logging.getLogger(__name__)

class DocumentUseCases(IDocument):
    """
    Use Case layer untuk orchestrating RAG pipeline (Document ingestion).
    Phases: Chunking → Embedding → Persist
    """
    def __init__(self, chunker: IChunker, collection_use_case: ICollection,embedder: BGEM3Embedder, qdrant: QdrantRepository):
        self._chunker = chunker
        self._embedder = embedder
        self._qdrant = qdrant
        self._collection_use_case = collection_use_case

    def ingest_document(self, raw_doc: dict, metadata: dict) -> Tuple[bool, str]:
        topic_label = metadata.get("topic", raw_doc.get("topic", "unknown"))[:50]

        # ── Phase 1: Chunking ─────────────────────────────────────────────
        try:
            chunks = self._chunker.chunk_document(raw_doc, extra_metadata=metadata)
            if not chunks:
                return False, "Dokumen menghasilkan 0 chunks setelah processing"

            logger.info(f"[CHUNK] '{topic_label}' → {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"[CHUNK] error: {e}", exc_info=True)
            return False, f"Chunking failed: {str(e)}"

        # ── Phase 2: Embedding ────────────────────────────────────────────
        try:
            texts = [chunk.page_content for chunk in chunks]
            logger.info(f"[EMBED] Embedding {len(texts)} chunks...")

            embeddings = self._embedder.embed_documents(texts)
            dense_vecs = embeddings["dense"]
            sparse_vecs = embeddings.get("sparse", [{}] * len(texts))

            for chunk, dense, sparse in zip(chunks, dense_vecs, sparse_vecs):
                chunk.metadata["dense_vector"] = dense
                chunk.metadata["sparse_vector"] = sparse

        except Exception as e:
            logger.critical(f"[EMBED] gagal: {e}", exc_info=True)
            return False, f"Embedding failed: {str(e)}"

        # ── Phase 3: Persist ke Vector Store ──────────────────────────────
        try:
            active_col = self._collection_use_case.get_active()
            saved_count = self._qdrant.persist_chunks(chunks, collection_name=active_col.name)
        except Exception as e:
            logger.error(f"[PERSIST] error: {e}", exc_info=True)
            return False, f"Persist failed: {str(e)}"

        return True, f"Berhasil menyimpan {saved_count} chunks"

    def retrieve(self, query: str, metadata: dict | None = None) -> tuple[bool, Any]:
        if not query.strip():
            return False, "Query tidak boleh kosong"

        metadata = metadata or {}
        limit = metadata.get("limit", 3)

        try:
            embeddings = self._embedder.embed_documents([query])

            dense_query = embeddings["dense"][0]
            sparse_query = embeddings["sparse"][0]

            active_col = self._collection_use_case.get_active()

            hits = self._qdrant.hybrid_search(
                dense_vector=dense_query,
                collection_name=active_col.name,
                sparse_vector=sparse_query,
                limit=limit
            )

            formatted_hits = [
                {
                    "id": hit["id"],
                    "score": hit["score"],
                    "payload": hit["payload"]
                } 
                for hit in hits
            ]
            return True, formatted_hits

        except Exception:
            logger.exception("[RETRIEVE] failed")
            return False, "Retrieval failed"