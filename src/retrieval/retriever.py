import logging
from typing import List, Dict, Any, Optional
from src.embeddings.vector_store import DocumentIndexer, EmbeddingModel

logger = logging.getLogger(__name__)

class RetrievalSystem:
    def __init__(self, vector_store_path: str = "./data/chroma_db"):
        self.indexer = DocumentIndexer(vector_store_path)
        self.top_k = 5

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """En ilgili belgeleri getir"""
        k = top_k or self.top_k
        results = self.indexer.search(query, top_k=k)
        
        return [
            {
                "content": r["text"],
                "source": r["metadata"].get("source") if r.get("metadata") else None,
                "chunk_id": r["metadata"].get("chunk_id") if r.get("metadata") else None,
                "relevance_score": 1 - r.get("distance", 1.0)
            }
            for r in results
        ]

    def format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Retrieval sonuçlarını bağlam formatında getir"""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.get("source", "Bilinmiyor")
            score = doc.get("relevance_score", 0)
            
            context_parts.append(
                f"--- Kaynak {i} ({source}, %.2f güven) ---\n{doc['content']}"
            )
        
        return "\n\n".join(context_parts)


class QueryProcessor:
    def __init__(self):
        self.retrieval_system = None

    def set_retrieval(self, vector_store_path: str):
        """Retrieval sistemini ayarla"""
        self.retrieval_system = RetrievalSystem(vector_store_path)

    def process_query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Sorguyu işle"""
        if self.retrieval_system is None:
            raise ValueError("Retrieval sistemi başlatılmadı")
        
        retrieved_docs = self.retrieval_system.retrieve(query, top_k=top_k)
        
        context = self.retrieval_system.format_context(retrieved_docs)
        
        return {
            "query": query,
            "retrieved_documents": retrieved_docs,
            "context": context,
            "num_docs": len(retrieved_docs)
        }