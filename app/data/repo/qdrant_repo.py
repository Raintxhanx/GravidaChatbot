from qdrant_client import QdrantClient
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid
from app.domain.document.interfaces import IVectorRepository

class QdrantRepository(IVectorRepository):
    def __init__(self, client: QdrantClient, collection_name: str):
        self._client = client
        self._collection = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """Infrastruktur: Memastikan tabel vector (collection) tersedia"""
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    def save(self, vector: list[float], content: str, metadata: dict) -> None:
        """Implementasi spesifik Qdrant untuk menyimpan data"""
        self._client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={"content": content, **metadata}
                )
            ]
        )

    def search(self, query_vector: list[float], limit: int = 3) -> list[dict]:
        """Implementasi spesifik Qdrant untuk mencari kemiripan vector (API Baru)"""
        
        # Gunakan query_points (pengganti search di qdrant-client terbaru)
        # Perhatikan parameternya sekarang bernama 'query', bukan 'query_vector'
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=limit
        )
        
        results = []
        
        # Hasil pencarian sekarang ada di dalam properti .points
        for hit in response.points:
            results.append({
                "score": hit.score, 
                "content": hit.payload.get("content", ""),
                "metadata": hit.payload
            })
            
        return results

def get_qdrant_client():
    # Logika koneksi dipusatkan di sini
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    # Jika menggunakan Cloudflare/HTTPS, port biasanya 443
    port = int(os.getenv("QDRANT_PORT", 443)) 
    
    return QdrantClient(
        url=url,
        api_key=api_key,
        port=port
    )