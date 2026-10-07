import pytest
from app.retrieval.notebooklm_engine import notebooklm_engine
from app.retrieval.hybrid_search import hybrid_search_engine
from app.generation.answer_generator import answer_generator


def test_notebooklm_engine_initialization():
    assert notebooklm_engine is not None
    # Authentication check should execute cleanly without raising exceptions
    auth_status = notebooklm_engine.is_authenticated()
    assert isinstance(auth_status, bool)


def test_hybrid_search_with_notebooklm_graceful():
    # Verify that hybrid search runs smoothly whether NotebookLM is logged in or not
    results, confidence = hybrid_search_engine.search(
        query="Gayatri Mantra ke 24 akshar kya hain?",
        top_k=3,
        use_hybrid=True,
        use_notebooklm=True,
    )
    assert len(results) > 0
    assert confidence in ("high", "medium")


def test_answer_generator_fallback_guarantee():
    # If NotebookLM is not authenticated, answer_generator must not crash and fallback to local pipeline
    from app.db.models import SearchResultItem
    sample_chunk = SearchResultItem(
        chunk_id="test_chunk_01",
        document_id="doc_test",
        content="गायत्री महाविज्ञान में २४ अक्षरों का विस्तृत वर्णन है।",
        score=0.9,
        metadata={"book": "गायत्री महाविज्ञान", "page_start": 1, "page_end": 1},
    )
    response = answer_generator.generate_answer(
        question="२४ अक्षर क्या हैं?",
        retrieved_items=[sample_chunk],
        retrieval_confidence="high",
        language="hi",
    )
    assert response is not None
    # Must either be supported, or gracefully return safe canonical abstention if free upstream API is rate-limited
    assert response.evidence_status in ("supported", "partial_support", "insufficient_evidence")
    assert response.answer is not None and len(response.answer) > 0
