import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMConfig:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))

    def is_configured(self) -> bool:
        return bool(self.api_key) or self.provider == "ollama"


class PromptTemplate:
    SYSTEM_PROMPT = """Sen şirket belgeleri üzerinden cevap veren bir yapay zeka asistanısın.
Görevin, kullanıcının sorusuna en iyi şekilde cevap vermektir.

Kurallar:
1. Sadece aşağıda verilen belgelerden bilgi kullanarak cevap ver
2. Eğer belgelerde cevap yoksa, "Bu konuda belgelerde bilgi bulunmuyor" de
3. Kaynak gösterdiğin bilgilerin doğru olduğundan emin ol
4. Verdiğin bilgiyi kaynak belgenin numarasıyla belirt

Yanıtın şu formatta olsun:
- Önce kısa ve net bir cevap
- Sonra detaylı açıklama (gerekirse)
- En son kaynaklar"""

    USER_PROMPT_TEMPLATE = """Soru: {question}

İlgili Belgeler:
{context}

Yukarıdaki belgeleri kullanarak soruyu cevapla."""

    def build_prompt(self, question: str, context: str) -> Dict[str, str]:
        return {
            "system": self.SYSTEM_PROMPT,
            "user": self.USER_PROMPT_TEMPLATE.format(
                question=question,
                context=context
            )
        }


class OpenAILLM:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None

    def initialize(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=self.config.api_key)

    def generate(self, prompt: Dict[str, str], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.client is None:
            self.initialize()

        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ]

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        return {
            "answer": response.choices[0].message.content,
            "model": self.config.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "timestamp": datetime.now().isoformat()
        }


class LLMResponse:
    def __init__(self, answer: str, sources: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.answer = answer
        self.sources = sources
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "metadata": self.metadata
        }

    def format_for_display(self) -> str:
        output = [self.answer, "\n--- Kaynaklar ---"]
        
        for i, source in enumerate(self.sources, 1):
            output.append(f"{i}. {source.get('source', 'Bilinmiyor')}")
        
        return "\n".join(output)


class LLMGenerator:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.llm = None
        self.prompt_template = PromptTemplate()

        if self.config.provider == "openai":
            self.llm = OpenAILLM(self.config)
        else:
            raise ValueError(f"Desteklenmeyen provider: {self.config.provider}")

    def generate(self, question: str, retrieved_docs: List[Dict[str, Any]]) -> LLMResponse:
        context = self._build_context(retrieved_docs)
        prompt = self.prompt_template.build_prompt(question, context)
        
        result = self.llm.generate(prompt, retrieved_docs)
        
        sources = [
            {
                "source": doc.get("source"),
                "chunk_id": doc.get("chunk_id"),
                "relevance": doc.get("relevance_score")
            }
            for doc in retrieved_docs
        ]
        
        return LLMResponse(
            answer=result["answer"],
            sources=sources,
            metadata={
                "model": result["model"],
                "usage": result["usage"],
                "timestamp": result["timestamp"]
            }
        )

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            source = doc.get("source", "Bilinmiyor")
            content = doc.get("content", "")
            
            context_parts.append(
                f"[Kaynak {i} - {source}]\n{content}\n"
            )
        
        return "\n\n".join(context_parts)