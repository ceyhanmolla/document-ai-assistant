import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        self.patterns = {
            "multiple_spaces": r'\s+',
            "multiple_newlines": r'\n\n+',
            "special_chars": r'[^\w\s\dığüşöçİĞÜŞÖÇ.,!?;:\-\(\)\[\]"]+',
        }

    def clean(self, text: str) -> str:
        """Metni temizle"""
        text = self._remove_multiple_spaces(text)
        text = self._remove_multiple_newlines(text)
        text = self._remove_special_chars(text)
        text = text.strip()
        return text

    def _remove_multiple_spaces(self, text: str) -> str:
        return re.sub(self.patterns["multiple_spaces"], " ", text)

    def _remove_multiple_newlines(self, text: str) -> str:
        return re.sub(self.patterns["multiple_newlines"], "\n", text)

    def _remove_special_chars(self, text: str) -> str:
        return re.sub(self.patterns["special_chars"], "", text)

    def normalize(self, text: str) -> str:
        """Metni normalize et"""
        text = text.lower()
        text = text.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
        return text


class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[dict]:
        """Metni parçalara böl"""
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "char_count": len(current_chunk)
                    })
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "char_count": len(current_chunk)
            })
        
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Metni cümlelere böl"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]