import pytest
from app.retrieval.query_normalizer import query_normalizer
from app.retrieval.hybrid_search import hybrid_search_engine
from app.generation.citation_validator import citation_validator
from app.generation.prompts import STRICT_SYSTEM_PROMPT, build_context_block


def test_query_normalizer_multilingual_terms():
    # Test Hinglish transliterated terms
    expanded, terms, detected_lang = query_normalizer.normalize_query("Pancha-Kosha aur Savita dhyan kya hai?")
    assert detected_lang in ("hinglish", "en", "hi")
    assert "पंचकोश" in expanded or "pancha-kosha" in expanded.lower()

    # Test English query terms
    expanded_en, _, _ = query_normalizer.normalize_query("How does Gayatri Raksha-Kavach protect spiritual seekers?")
    assert "रक्षा-कवच" in expanded_en or "raksha-kavach" in expanded_en.lower()


def test_retrieval_hinglish_coverage():
    query = "Gayatri Mantra ke 24 akshar human body se kaise connected hain?"
    results, confidence = hybrid_search_engine.search(query=query, top_k=3, use_hybrid=True)
    assert len(results) > 0
    assert confidence in ("high", "medium")
    top_chunk = results[0]
    assert any(term in top_chunk.content.lower() for term in ["24", "granthi", "akshar", "nerve"])


def test_retrieval_english_coverage():
    query = "What is the literal and spiritual word-by-word meaning of the Gayatri Mantra?"
    results, confidence = hybrid_search_engine.search(query=query, top_k=3, use_hybrid=True)
    assert len(results) > 0
    assert confidence in ("high", "medium")
    top_chunk = results[0]
    assert any(term in top_chunk.content.lower() for term in ["om", "tat", "savituh", "varenyam", "meaning"])


def test_retrieval_safe_abstention_on_irrelevant():
    query = "What are the latest stock market trends in NASDAQ and crypto trading algorithms?"
    results, confidence = hybrid_search_engine.search(query=query, top_k=3, use_hybrid=True)
    assert confidence == "insufficient_evidence" or len(results) == 0


def test_multilingual_citation_provenance():
    results, _ = hybrid_search_engine.search("Gayatri Mantra ke har ek shabd ka meaning", top_k=2)
    assert len(results) > 0
    top_res = results[0]
    resolved = citation_validator.resolve_citation(top_res.chunk_id)
    assert resolved is not None
    assert resolved.book is not None
    assert "गायत्री महाविज्ञान" in resolved.book
