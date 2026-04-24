import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    query: str
    expected_topics: List[str]
    min_relevant: int = 1

@dataclass
class TestResult:
    query: str
    passed: bool
    relevant_docs: int
    retrieved_sources: List[str]
    avg_relevance: float
    errors: List[str]


class RetrievalEvaluator:
    def __init__(self, query_processor):
        self.query_processor = query_processor
    
    def evaluate_query(self, query: str, expected_topics: List[str], min_relevant: int = 1) -> TestResult:
        try:
            result = self.query_processor.process_query(query, top_k=10)
            docs = result.get("retrieved_documents", [])
            
            relevant_count = 0
            sources = []
            relevances = []
            
            for doc in docs:
                content = doc.get("content", "").lower()
                source = doc.get("source", "unknown")
                relevance = doc.get("relevance_score", 0)
                
                sources.append(source)
                relevances.append(relevance)
                
                for topic in expected_topics:
                    if topic.lower() in content:
                        relevant_count += 1
                        break
            
            avg_relevance = sum(relevances) / len(relevances) if relevances else 0
            
            return TestResult(
                query=query,
                passed=relevant_count >= min_relevant,
                relevant_docs=relevant_count,
                retrieved_sources=sources,
                avg_relevance=avg_relevance,
                errors=[]
            )
        
        except Exception as e:
            logger.error(f"Test hatası: {e}")
            return TestResult(
                query=query,
                passed=False,
                relevant_docs=0,
                retrieved_sources=[],
                avg_relevance=0,
                errors=[str(e)]
            )

    def run_test_suite(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        results = []
        
        for test in test_cases:
            result = self.evaluate_query(test.query, test.expected_topics, test.min_relevant)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": [
                {
                    "query": r.query,
                    "passed": r.passed,
                    "relevant_docs": r.relevant_docs,
                    "avg_relevance": r.avg_relevance,
                    "errors": r.errors
                }
                for r in results
            ]
        }


def run_quality_tests(vector_store_path: str = "./data/chroma_db", test_queries: List[Dict[str, Any]] = None):
    from src.retrieval.retriever import QueryProcessor
    
    processor = QueryProcessor()
    processor.set_retrieval(vector_store_path)
    
    if test_queries is None:
        test_queries = [
            {"query": "izin politikası", "expected": ["izin", "izın"]},
            {"query": "maaş", "expected": ["maaş", "ücret"]},
            {"query": "çalışma saatleri", "expected": ["çalışma", "saat"]},
        ]
    
    test_cases = [
        TestCase(
            query=t["query"],
            expected_topics=t["expected"],
            min_relevant=1
        )
        for t in test_queries
    ]
    
    evaluator = RetrievalEvaluator(processor)
    results = evaluator.run_test_suite(test_cases)
    
    return results


if __name__ == "__main__":
    print("📊 Retrieval Kalite Testleri")
    print("=" * 50)
    
    results = run_quality_tests()
    
    print(f"\nToplam: {results['total_tests']}")
    print(f"Geçen: {results['passed']}")
    print(f"Kalan: {results['failed']}")
    print(f"Başarı oranı: {results['pass_rate']:.1%}")
    
    print("\n--- Detaylı Sonuçlar ---")
    for r in results["results"]:
        status = "✓" if r["passed"] else "✗"
        print(f"{status} {r['query']}: {r['relevant_docs']} ilgili, {r['avg_relevance']:.2f} ortlama")