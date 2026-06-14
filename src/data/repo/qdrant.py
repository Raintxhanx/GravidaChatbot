import logging
import uuid
from typing import List
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, 
    VectorParams, 
    SparseVectorParams, 
    SparseVector, 
    Distance, 
    Prefetch, 
    FusionQuery, 
    Fusion
)

logger = logging.getLogger(__name__)

class QdrantRepository:
    def __init__(self, url: str = "http://localhost", port: int = 443, api_key: str = None):
        self.url = url
        self.port = port
        self._client = QdrantClient(url=self.url, port=self.port, api_key=api_key)

    def ensure_collection(self, collection_name: str):
        """Membuat collection dengan dukungan Hybrid (Dense + Sparse) jika belum ada"""
        try:
            if not self._client.collection_exists(collection_name):
                self._client.create_collection(
                    collection_name=collection_name,
                    # Menggunakan Named Vectors untuk Dense
                    vectors_config={
                        "dense": VectorParams(size=1024, distance=Distance.COSINE) # BGE-M3 Dense = 1024
                    },
                    # Menambahkan konfigurasi untuk Sparse
                    sparse_vectors_config={
                        "sparse": SparseVectorParams()
                    }
                )
                logger.info(f"[QDRANT REPOSITORY] Collection '{collection_name}' berhasil dibuat dengan mode Hybrid.")
        except Exception as e:
            logger.error(f"[QDRANT REPOSITORY] Gagal memastikan/membuat collection '{collection_name}': {e}")
            raise e

    def _format_sparse_vector(self, sparse_data: dict) -> SparseVector:
        """Helper untuk konversi output sparse BGE-M3 ke format Qdrant SparseVector"""
        if "indices" in sparse_data and "values" in sparse_data:
            return SparseVector(indices=sparse_data["indices"], values=sparse_data["values"])
        
        indices = [int(k) for k in sparse_data.keys()]
        values = [float(v) for v in sparse_data.values()]
        return SparseVector(indices=indices, values=values)

    def persist_chunks(self, chunks: List[Document], collection_name: str) -> int:
        """Menyimpan chunks dengan multi-vector (dense dan sparse)"""
        if not chunks:
            return 0

        # Pastikan collection sudah dibuat terlebih dahulu secara aman
        self.ensure_collection(collection_name)

        logger.info(f"[QDRANT REPOSITORY] Menyimpan {len(chunks)} chunks ke collection: {collection_name}")
        points = []

        for i, chunk in enumerate(chunks):
            assert "dense_vector" in chunk.metadata, f"Chunk[{i}] kehilangan dense_vector!"
            assert "sparse_vector" in chunk.metadata, f"Chunk[{i}] kehilangan sparse_vector!"
            
            dense_vector = chunk.metadata.pop("dense_vector")
            sparse_raw = chunk.metadata.pop("sparse_vector")
            
            # Format sparse ke objek Qdrant
            sparse_vector = self._format_sparse_vector(sparse_raw)

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        "dense": dense_vector,
                        "sparse": sparse_vector
                    },
                    payload={
                        "content": chunk.page_content,
                        **chunk.metadata
                    }
                )
            )

        self._client.upsert(
            collection_name=collection_name,
            points=points
        )
        return len(chunks)

    def hybrid_search(self, dense_vector: list[float], sparse_vector: dict, collection_name: str, limit: int = 3) -> list[dict]:
        """Pencarian Hybrid menggunakan query_points + RRF (Reciprocal Rank Fusion)"""
        logger.info(f"[QDRANT REPOSITORY] Melakukan hybrid search pada collection: {collection_name}")
        
        formatted_sparse = self._format_sparse_vector(sparse_vector)

        # Menggunakan Prefetch untuk mengambil kandidat dari masing-masing jenis search
        response = self._client.query_points(
            collection_name=collection_name,
            prefetch=[
                Prefetch(query=dense_vector, using="dense", limit=limit * 2),
                Prefetch(query=formatted_sparse, using="sparse", limit=limit * 2)
            ],
            # Menggabungkan hasil menggunakan Reciprocal Rank Fusion (RRF)
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit
        )
        
        results = []
        for hit in response.points:
            results.append({
                "id": hit.id,  #  TAMBAHKAN INI agar ID tidak hilang
                "score": hit.score,
                "payload": hit.payload  # Ubah nama key jadi payload agar konsisten dengan penamaan Qdrant
            })
            
        return results