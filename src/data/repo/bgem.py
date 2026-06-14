import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.embeddings import Embeddings
from FlagEmbedding import BGEM3FlagModel

logger = logging.getLogger(__name__)

class BGEM3Embedder():
    MODEL_NAME = "BAAI/bge-m3"
    EMBEDDING_DIM = 1024

    def __init__(
        self,
        use_fp16: bool = True,
        batch_size: int = 12,
        max_length: int = 8192,
        device: Optional[str] = None,
    ):
        self.batch_size = batch_size
        self.max_length = max_length
        
        # 1. Setup path cache
        base_path = Path(os.getcwd()) / 'model_data'
        base_path.mkdir(exist_ok=True)

        logger.info(f"Loading {self.MODEL_NAME} (fp16={use_fp16}, cache_dir={base_path})...")

        # 2. Cek apakah folder model offline sudah eksis
        hf_folder_name = f"models--{self.MODEL_NAME.replace('/', '--')}"
        snapshots_dir = base_path / hf_folder_name / 'snapshots'
        actual_local_path = None

        if snapshots_dir.exists() and snapshots_dir.is_dir():
            try:
                subfolders = [f for f in snapshots_dir.iterdir() if f.is_dir()]
                if subfolders:
                    actual_local_path = str(subfolders[0])
            except Exception as e:
                logger.warning(f"Gagal membaca folder snapshot: {e}")

        # 3. Load model secara dinamis
        if actual_local_path:
            print(f" [OFFLINE] Menggunakan model lokal dari: {actual_local_path}")
            # PERBAIKAN: Masukkan juga use_fp16 dan device agar konsisten
            self._model = BGEM3FlagModel(
                actual_local_path,
                use_fp16=use_fp16,
                device=device
            )
        else:
            print(f" [ONLINE] Model tidak ditemukan di lokal. Men-download dari HuggingFace...")
            # Akan otomatis download dan menyimpannya di cache_dir
            self._model = BGEM3FlagModel(
                self.MODEL_NAME, 
                use_fp16=use_fp16, 
                device=device,
                cache_dir=str(base_path)
            )
            
        logger.info(f"✅ {self.MODEL_NAME} loaded — dim={self.EMBEDDING_DIM}")

    def embed_documents(self, texts: List[str], return_sparse: bool = True) -> Dict[str, Any]:
        if not texts:
            return {"dense": [], "sparse": []}

        texts = [self._preprocess(t) for t in texts]
        output = self._model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=self.max_length,
            return_dense=True,
            return_sparse=return_sparse,
            return_colbert_vecs=False,
        )

        result: Dict[str, Any] = {"dense": output["dense_vecs"].tolist()}
        if return_sparse:
            result["sparse"] = self._convert_sparse(output["lexical_weights"])
        return result

    def embed_query(self, text: str, return_sparse: bool = True) -> Dict[str, Any]:
        text = self._preprocess(text)
        output = self._model.encode(
            [text],
            batch_size=1,
            max_length=self.max_length,
            return_dense=True,
            return_sparse=return_sparse,
            return_colbert_vecs=False,
        )

        result: Dict[str, Any] = {"dense": output["dense_vecs"][0].tolist()}
        if return_sparse:
            result["sparse"] = self._convert_sparse(output["lexical_weights"])[0]
        return result

    @staticmethod
    def _preprocess(text: str) -> str:
        return text.strip().replace("\n\n", "\n")

    @staticmethod
    def _convert_sparse(lexical_weights) -> List[Dict[int, float]]:
        return [{int(k): float(v) for k, v in w.items()} for w in lexical_weights]


class BGELangChainEmbeddings(Embeddings):
    """Drop-in LangChain Embeddings wrapper untuk BGEM3Embedder (dense only)."""

    def __init__(self, embedder: BGEM3Embedder):
        self._embedder = embedder

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embedder.embed_documents(texts, return_sparse=False)["dense"]

    def embed_query(self, text: str) -> List[float]:
        return self._embedder.embed_query(text, return_sparse=False)["dense"]