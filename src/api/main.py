from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "./data"
UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/chroma_db")

# Lazy-loaded singletons
_loader = None
_cleaner = None
_chunker = None
_indexer = None
_query_processor = None
_llm_generator = None


def get_loader():
    global _loader
    if _loader is None:
        from src.utils.loader import DocumentLoader
        _loader = DocumentLoader()
    return _loader

def get_cleaner():
    global _cleaner
    if _cleaner is None:
        from src.utils.processor import TextCleaner
        _cleaner = TextCleaner()
    return _cleaner

def get_chunker():
    global _chunker
    if _chunker is None:
        from src.utils.processor import TextChunker
        _chunker = TextChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    return _chunker

def get_indexer():
    global _indexer
    if _indexer is None:
        from src.embeddings.vector_store import DocumentIndexer
        _indexer = DocumentIndexer(VECTOR_STORE_PATH)
    return _indexer

def get_query_processor():
    global _query_processor
    if _query_processor is None:
        from src.retrieval.retriever import QueryProcessor
        _query_processor = QueryProcessor()
        _query_processor.set_retrieval(VECTOR_STORE_PATH)
    return _query_processor

def get_llm_generator():
    global _llm_generator
    if _llm_generator is None:
        from src.llm.generator import LLMGenerator, LLMConfig
        config = LLMConfig()
        if config.is_configured():
            _llm_generator = LLMGenerator(config)
            logger.info("LLM başlatıldı")
        else:
            logger.warning("LLM yapılandırılmadı - .env dosyasını kontrol edin")
    return _llm_generator


@app.get("/")
async def root():
    return {"message": "Document AI Assistant API", "version": "1.0.0"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        loader = get_loader()
        cleaner = get_cleaner()
        chunker = get_chunker()
        indexer = get_indexer()
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        text = loader.load_document(file_path)
        text = cleaner.clean(text)
        chunks = chunker.chunk(text)
        
        source_name = os.path.splitext(file.filename)[0]
        result = indexer.index_documents(chunks, source_name)
        
        return {
            "status": "success",
            "message": f"Belge yüklendi: {file.filename}",
            "chunks": len(chunks),
            "indexed": result
        }
    
    except Exception as e:
        logger.error(f"Yükleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/query")
async def query_document(query: str, top_k: int = 5):
    try:
        query_processor = get_query_processor()
        result = query_processor.process_query(query, top_k=top_k)
        
        llm_gen = get_llm_generator()
        if llm_gen:
            llm_result = llm_gen.generate(query, result["retrieved_documents"])
            return llm_result.to_dict()
        else:
            return {
                "answer": None,
                "retrieved_documents": result["retrieved_documents"],
                "context": result["context"],
                "note": "LLM yapılandırılmadı"
            }
    
    except Exception as e:
        logger.error(f"Sorgu hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/search")
async def search_documents(query: str, top_k: int = 5):
    try:
        query_processor = get_query_processor()
        result = query_processor.process_query(query, top_k=top_k)
        return result
    
    except Exception as e:
        logger.error(f"Arama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/status")
async def get_status():
    return {
        "status": "ready",
        "upload_dir": UPLOAD_DIR,
        "vector_store": VECTOR_STORE_PATH
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)