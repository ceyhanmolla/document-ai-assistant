#!/bin/bash

echo "🚀 Document AI Assistant Başlatılıyor..."

# 1. Backend API'yi başlat (arka planda)
echo "📡 Backend API başlatılıyor..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 2. Sağlamlaşma için bekle
sleep 3

# 3. Health check
curl -s http://localhost:8000/ > /dev/null && echo "✅ API hazır" || echo "❌ API başlatılamadı"

echo ""
echo "🎯 Başlatma tamamlandı!"
echo "📋 API: http://localhost:8000"
echo "📋 API Docs: http://localhost:8000/docs"
echo "📋 Frontend (Streamlit): streamlit run src/ui/app.py"
echo ""
echo "💡 Sonraki adımlar:"
echo "   1. Frontend'i yeni terminalde başlatın"
echo "   2. Tarayıcıda http://localhost:8501 açın"
echo "   3. Belge yükleyip sorular sorun"
echo ""
echo "⏹ API'yi durdurmak için: kill $API_PID"

# PID'i dosyaya yaz
echo $API_PID > .api.pid