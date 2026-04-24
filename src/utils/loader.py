import os
import logging
from pathlib import Path
from typing import List, Optional
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self):
        self.supported_extensions = {".pdf", ".docx", ".txt", ".md"}

    def load_document(self, file_path: str) -> str:
        """Belgeyi yükle ve metin çıkar"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
        
        if path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"Desteklenmeyen format: {path.suffix}")
        
        if path.suffix.lower() == ".pdf":
            return self._extract_from_pdf(file_path)
        elif path.suffix.lower() in [".docx", ".doc"]:
            return self._extract_from_docx(file_path)
        elif path.suffix.lower() in [".txt", ".md"]:
            return self._extract_from_txt(file_path)
        
        return ""

    def _extract_from_pdf(self, file_path: str) -> str:
        """PDF'den metin çıkar"""
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF okuma hatası: {e}")
            raise
        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """Word belgesinden metin çıkar"""
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            logger.error(f"Word okuma hatası: {e}")
            raise
        return text

    def _extract_from_txt(self, file_path: str) -> str:
        """Txt/Markdown dosyasından metin çıkar"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"TXT okuma hatası: {e}")
            raise

    def load_directory(self, directory: str) -> List[dict]:
        """Klasördeki tüm belgeleri yükle"""
        docs = []
        dir_path = Path(directory)
        
        for file_path in dir_path.rglob("*"):
            if file_path.suffix.lower() in self.supported_extensions:
                try:
                    content = self.load_document(str(file_path))
                    docs.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "content": content,
                        "type": file_path.suffix.lower()
                    })
                except Exception as e:
                    logger.warning(f"Dosya atlandı: {file_path.name} - {e}")
        
        return docs