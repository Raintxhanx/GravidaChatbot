import fitz
from typing import List, Dict, Any
from app.domain.document.interfaces import IDocumentParser

class PyMuPDFParser(IDocumentParser):
    def extract_text_from_pdf(self, file_stream) -> List[Dict[str, Any]]:
        doc = fitz.open(stream=file_stream, filetype="pdf")
        pages = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pages.append({
                "page_num": page_num + 1,
                "text": page.get_text()
            })
        return pages