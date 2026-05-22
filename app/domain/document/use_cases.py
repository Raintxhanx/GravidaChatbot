import re
from typing import List, Dict, Any
from .interfaces import IVectorRepository, IEmbeddingService, ITextSplitter, IDocumentParser

class RAGApplicationService:
    def __init__(
        self, 
        repository: IVectorRepository, 
        embedder: IEmbeddingService,
        text_splitter: ITextSplitter,
        doc_parser: IDocumentParser
    ):
        self._repository = repository
        self._embedder = embedder
        self._text_splitter = text_splitter
        self._doc_parser = doc_parser

    def ingest_document(self, text: str, metadata: dict):
        if not text.strip():
            return False, "Teks kosong atau tidak valid"
            
        try:
            vector = self._embedder.get_embedding(text)
            self._repository.save(vector, text, metadata)
            return True, "Dokumen berhasil diproses dan disimpan"
        except Exception as e:
            return False, f"Terjadi kesalahan: {str(e)}"

    def ingest_pdf(self, file_stream, metadata: dict) -> dict:
        """Logic Bisnis: Extract -> Chunk -> Embed -> Store dengan pelacakan error"""
        total_processed = 0
        errors = []
        
        try:
            pages = self._doc_parser.extract_text_from_pdf(file_stream)
            
            for page_data in pages:
                page_num = page_data['page_num']
                raw_text = page_data['text']
                
                if not raw_text.strip():
                    continue

                clean_text = re.sub(r'[ \t]+', ' ', raw_text)
                chunks = self._text_splitter.split_text(clean_text)
                
                for i, chunk_text in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "page": page_num,
                        "chunk_index": i,
                        "total_pages": len(pages)
                    })
                    
                    # VALIDASI DAN VERIFIKASI HASIL INGESTION
                    success, msg = self.ingest_document(chunk_text, chunk_metadata)
                    if success:
                        total_processed += 1
                    else:
                        errors.append(f"Gagal di halaman {page_num}, chunk {i}: {msg}")

            return {
                "success": len(errors) == 0,
                "status": "success" if not errors else "partial_success",
                "total_chunks_saved": total_processed,
                "errors": errors
            }
        except Exception as e:
            return {
                "success": False,
                "status": "failed",
                "total_chunks_saved": total_processed,
                "errors": [f"Gagal memproses PDF secara sistem: {str(e)}"]
            }

    def ingest_json_batch(self, data_list: list[dict]) -> dict:
        total_processed = 0
        errors = []

        for item in data_list:
            text = item.get("text", "")
            metadata = item.get("metadata", {})
            
            if not text:
                errors.append(f"Teks kosong pada doc_id: {metadata.get('doc_id', 'unknown')}")
                continue
                
            clean_text = re.sub(r'[ \t]+', ' ', text)
            chunks = self._text_splitter.split_text(clean_text)
            
            for i, chunk_text in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({"chunk_index": i})
                
                # Memastikan block try-except di ingest_document bekerja optimal
                success, msg = self.ingest_document(chunk_text, chunk_metadata)
                if success:
                    total_processed += 1
                else:
                    errors.append(f"Gagal di chunk {i} (doc: {metadata.get('doc_id', 'unknown')}): {msg}")

        return {
            "success": len(errors) == 0,
            "status": "success" if not errors else "partial_success",
            "total_chunks_saved": total_processed,
            "errors": errors
        }
    
    def retrieve_context(self, question: str, top_k: int = 3, score_threshold: float = 0.75) -> dict:
        if not question.strip():
            return {"success": False, "message": "Pertanyaan tidak boleh kosong", "context": "", "raw_data": []}

        try:
            query_vector = self._embedder.get_query_embedding(question)
            raw_results = self._repository.search(query_vector=query_vector, limit=top_k)

            formatted_context = ""
            filtered_results = []

            for idx, res in enumerate(raw_results):
                if res['score'] >= score_threshold:
                    filtered_results.append(res)
                    source = res['metadata'].get('source', 'Dokumen Internal')
                    formatted_context += f"[Referensi {idx+1} | Skor: {res['score']:.2f} | Sumber: {source}]\n"
                    formatted_context += f"{res['content']}\n\n"

            if not formatted_context:
                formatted_context = "Tidak ada informasi relevan yang ditemukan di dalam database medis."

            return {
                "success": True,
                "context": formatted_context.strip(),
                "raw_data": filtered_results
            }
        except Exception as e:
            return {"success": False, "message": f"Gagal melakukan retrieval: {str(e)}", "context": "", "raw_data": []}