import os
import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

    def load(self):
        """Modeli yükle"""
        if self.model is None:
            logger.info(f"Embedding modeli yükleniyor: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model başarıyla yüklendi")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Metinleri embedding vektörlerine dönüştür"""
        if self.model is None:
            self.load()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        return embeddings.tolist()


class VectorStore:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or "./data/chroma_db"
        self.client = None
        self.collection = None

    def initialize(self):
        """ChromaDB'yi başlat"""
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Belge parçaları vektör veritabanı"}
        )

    def add_documents(self, texts: List[str], ids: List[str], metadatas: Optional[List[dict]] = None):
        """Belge parçalarını ekle"""
        if self.client is None:
            self.initialize()
        
        if metadatas is None:
            metadatas = [{"source": f"doc_{i}"} for i in range(len(texts))]
        
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def similarity_search(self, query: str, n_results: int = 5) -> dict:
        """Benzerlik araması yap"""
        if self.client is None:
            self.initialize()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results

    def delete_all(self):
        """Tüm belgeleri sil"""
        if self.collection is not None:
            self.collection.delete(where={})


class DocumentVectorStore:
    def __init__(self, persist_directory: Optional[str] = None):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(persist_directory)

    def add_chunks(self, chunks: List[dict], source_name: str):
        """Parçaları vektör veritabanına ekle"""
        self.embedding_model.load()
        
        texts = [chunk["text"] for chunk in chunks]
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]
        
        metadatas = []
        for i, chunk in enumerate(chunks):
            meta = {
                "source": source_name,
                "chunk_id": i,
                "char_count": chunk.get("char_count", 0)
            }
            metadatas.append(meta)
        
        embeddings = self.embedding_model.embed(texts)
        
        if self.vector_store.client is None:
            self.vector_store.initialize()
        
        texts_with_ids = list(zip(ids, texts, metadatas))
        
        for i, text, meta in texts_with_ids:
            self.vector_store.collection.upsert(
                ids=[i],
                documents=[text],
                metadatas=[meta],
                embeddings=[embeddings[ids.index(i)]]
            )

from typing import List, Dict, Any

class DocumentIndexer:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(persist_directory)
        self.embedding_model.load()

    def index_documents(self, chunks: List[Dict[str, Any]], source_name: str):
        """Belgeleri indeksle"""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)
        
        ids = [f"{source_name}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": source_name,
                "chunk_id": i,
                "char_count": chunk.get("char_count", 0)
            }
            for i, chunk in enumerate(chunks)
        ]
        
        self.vector_store.initialize()
        self.vector_store.add_documents(texts, ids, metadatas)
        
        return f"{len(chunks)} parça indekslendi"

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Sorgu ile en benzer belgeleri bul"""
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        
        results = self.vector_store.similarity_search(query, n_results=top_k)
        
        documents = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "text": doc,
                    "id": results["ids"][0][i] if results.get("ids") else None,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else None,
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
        
        return documents