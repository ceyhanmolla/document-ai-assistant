# Document AI Assistant - Başlangıç Kılavuzu

## Hızlı Başlatma (2 Adım)

### 1. OpenAI API Anahtarı Ekleyin
```bash
# .env dosyasını düzenleyin
nano .env
# veya
code .env
```

OPENAI_API_KEY değerini ekleyin:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. Projeyi Başlatın

**Seçenek A - Otomatik (Tavsiye Edilen):**
```bash
./start.sh
```

**Seçenek B - Manuel:**
```bash
# Terminal 1 - Backend
uvicorn src.api.main:app --reload

# Terminal 2 - Frontend (ayrı terminalde)
streamlit run src/ui/app.py
```

## Kullanım

1. **Frontend'i açın:** http://localhost:8501
2. **Belge yükleyin:** PDF, DOCX, TXT formatlarında
3. **Sorular sorun:** "Şirketimizin izin politikası nedir?"

## API Endpoints

- `GET /` - API durumu
- `POST /documents/upload` - Belge yükle
- `POST /documents/query` - Sorgu ve LLM cevabı
- `GET /documents/search` - Sadece retrieval sonuçları
- `GET /documents/status` - Sistem durumu

## Proje Yapısı

```
document-ai-assistant/
├── data/
│   └── uploads/          # Yüklenen belgeler
├── src/
│   ├── api/              # FastAPI backend
│   ├── ui/               # Streamlit frontend
│   ├── utils/            # Belge yükleme
│   ├── embeddings/       # Vektör DB
│   ├── retrieval/        # Retrieval sistemi
│   └── llm/              # LLM entegrasyonu
├── start.sh              # Otomatik başlatma scripti
└── .env                  # API anahtarı buraya
```

## Hata Ayıklama

**API'ye bağlanamıyorum:**
- API çalışıyor mu kontrol edin: `curl http://localhost:8000`
- Port 8000 başka bir uygulama kullanıyor mu?

**Embedding modeli yüklenemiyor:**
- İlk kullanımda sentence-transformers modeli indirilir (yaklaşık 100MB)
- İnternet bağlantısı kontrol edin

**LLM cevabı gelmiyor:**
- `.env` dosyasında OPENAI_API_KEY doğru mu?
- OpenAI API kotalarınız dolmuş mu?

## Test

```bash
# Retrieval kalitesini test et
python src/tests/test_retrieval.py
```