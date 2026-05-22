from glob import glob
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.domain.document.interfaces import IEmbeddingService

class SentenceTransformerImpl(IEmbeddingService):
    def __init__(self, model_name):
        # Tembak langsung folder 'model_data' di root project secara absolut
        # Pastikan ini mengarah ke F:\Kuliah\Penulisan Ilmiah\Prototype Project\model_data
        base_path = Path(os.getcwd()) / 'model_data'
        
        # Format nama folder cache Hugging Face
        hf_folder_name = f"models--{model_name.replace('/', '--')}"
        snapshots_dir = base_path / hf_folder_name / 'snapshots'

        actual_local_path = None

        # Cek apakah folder snapshots ada
        if snapshots_dir.exists() and snapshots_dir.is_dir():
            # Ambil subfolder pertama di dalam snapshots (menggunakan pathlib iterdir)
            try:
                subfolders = [f for f in snapshots_dir.iterdir() if f.is_dir()]
                if subfolders:
                    actual_local_path = str(subfolders[0])
            except Exception:
                pass

        if actual_local_path:
            print(f" [OFFLINE] Menggunakan model lokal dari: {actual_local_path}")
            self.model = SentenceTransformer(actual_local_path)
        else:
            # Fallback jika cache belum terbentuk sempurna, atau folder kosong
            print(" [ONLINE] Model lokal tidak ditemukan atau belum lengkap. Mencoba download...")
            self.model = SentenceTransformer(
                model_name,
                cache_folder=str(base_path)
            )

    def get_embedding(self, text: str):
        # Format 'passage: ' sesuai standar model E5
        return self.model.encode(f"passage: {text}").tolist()
    
    def get_query_embedding(self, query: str):
        # Format 'query: ' khusus untuk RETRIEVAL / Pencarian
        return self.model.encode(f"query: {query}").tolist()