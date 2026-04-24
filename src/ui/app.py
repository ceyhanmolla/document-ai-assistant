import streamlit as st
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Document AI Assistant",
    page_icon="📚",
    layout="wide"
)


def check_api():
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_file(file):
    files = {"file": (file.name, file.getvalue(), file.type)}
    response = requests.post(f"{API_URL}/documents/upload", files=files)
    return response.json()


def query_document(query, top_k=5):
    response = requests.post(
        f"{API_URL}/documents/query",
        params={"query": query, "top_k": top_k}
    )
    return response.json()


def search_documents(query, top_k=5):
    response = requests.get(
        f"{API_URL}/documents/search",
        params={"query": query, "top_k": top_k}
    )
    return response.json()


st.title("📚 Document AI Assistant")
st.markdown("---")

api_status = check_api()

if not api_status:
    st.error("API'ye bağlanılamıyor. Lütfen önce API'yi başlatın:")
    st.code("uvicorn src.api.main:app --reload", language="bash")
    st.stop()

with st.sidebar:
    st.header("⚙️ Ayarlar")
    top_k = st.slider("Gösterilecek sonuç sayısı", 1, 10, 5)
    
    st.markdown("---")
    st.header("📊 Durum")
    st.info("API çalışıyor ✓")

tab1, tab2 = st.tabs(["💬 Soru Sorma", "📁 Belge Yükleme"])

with tab1:
    query = st.text_input("Sorunuzu yazın:", placeholder="Örnek: Şirketimizin izin politikası nedir?")
    
    if query:
        with st.spinner("Sorgu işleniyor..."):
            try:
                result = search_documents(query, top_k)
                
                st.subheader("📋 Bulunan Belgeler")
                
                for i, doc in enumerate(result.get("retrieved_documents", []), 1):
                    with st.expander(f"📄 Kaynak {i} - {doc.get('source', 'Bilinmiyor')}"):
                        st.markdown(f"**Güven Skoru:** {doc.get('relevance_score', 0):.2f}")
                        st.markdown(f"**İçerik:**\n{doc.get('content', '')}")
                
                st.markdown("---")
                st.subheader("🤖 LLM Cevabı")
                
                if result.get("note") == "LLM yapılandırılmadı":
                    st.warning("LLM yapılandırılmadı. .env dosyasında OPENAI_API_KEY ayarlayın.")
                else:
                    llm_result = query_document(query, top_k)
                    
                    st.markdown(llm_result.get("answer", "Cevap üretilemedi"))
                    
                    if llm_result.get("sources"):
                        st.subheader("📚 Kaynaklar")
                        for i, source in enumerate(llm_result["sources"], 1):
                            st.markdown(f"{i}. **{source.get('source', 'Bilinmiyor')}**")
            
            except Exception as e:
                st.error(f"Hata: {e}")

with tab2:
    uploaded_file = st.file_uploader(
        "Belge seçin:",
        type=["pdf", "docx", "txt", "md"]
    )
    
    if uploaded_file:
        if st.button("📤 Yükle"):
            with st.spinner("Belge işleniyor..."):
                try:
                    result = upload_file(uploaded_file)
                    
                    if result.get("status") == "success":
                        st.success(result.get("message"))
                        st.metric("Parça sayısı", result.get("chunks", 0))
                    else:
                        st.error(f"Hata: {result}")
                
                except Exception as e:
                    st.error(f"Yükleme hatası: {e}")
    
    st.markdown("---")
    st.info("💡 Desteklenen formatlar: PDF, DOCX, TXT, MD")

st.markdown("---")
st.caption(f"Document AI Assistant v1.0.0 | {datetime.now().strftime('%Y-%m-%d')}")