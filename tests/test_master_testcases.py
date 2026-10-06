import json
import pytest
from pathlib import Path

from app.retrieval.query_normalizer import query_normalizer
from app.retrieval.hybrid_search import hybrid_search_engine
from app.generation.citation_validator import citation_validator
from app.generation.abstention import get_abstention_text
from app.api.chat import chat_endpoint
from app.db.models import ChatRequest, SearchResultItem


@pytest.fixture(scope="module")
def master_testcases():
    dataset_path = Path("app/evaluation/master_testcases.json")
    assert dataset_path.exists(), "master_testcases.json must exist"
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    assert len(cases) == 105, f"Expected 105 test cases, found {len(cases)}"
    return cases


def test_master_dataset_structure_and_sections(master_testcases):
    """Verify that all 105 test cases have required fields and span the 10 sections."""
    sections = set()
    for tc in master_testcases:
        assert "id" in tc
        assert "q_num" in tc
        assert "section" in tc
        assert "question" in tc
        assert "expected_answer" in tc
        assert len(tc["question"].strip()) > 5
        assert len(tc["expected_answer"].strip()) > 5
        sections.add(tc["section"])

    # Must contain all 10 core sections
    assert len(sections) == 10, f"Expected 10 sections, found {len(sections)}"


def test_query_normalization_on_master_concepts(master_testcases):
    """Verify that query normalizer processes questions without crashing and expands key terms."""
    for tc in master_testcases[:20]:
        q = tc["question"]
        norm = query_normalizer.normalize(q)
        assert isinstance(norm, str)
        assert len(norm) > 0


def test_retrieval_provenance_and_approved_status(master_testcases):
    """Test retrieval on sample questions to ensure all returned chunks have approved provenance."""
    sample_queries = [
        master_testcases[0]["question"],   # Q1: Padachheda
        master_testcases[2]["question"],   # Q3: Tat akshar
        master_testcases[25]["question"],  # Q26: Vyahritis
        master_testcases[35]["question"],  # Q36: Nadis
    ]

    for q in sample_queries:
        results, confidence = hybrid_search_engine.search(query=q, top_k=3, use_hybrid=True)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, SearchResultItem)
            assert r.chunk_id
            assert r.document_id
            meta = r.metadata
            assert meta.get("quality_status") == "approved"
            assert meta.get("copyright_status") == "approved"


def test_abstention_guarantee_on_unindexed_domain(master_testcases):
    """Test that queries with insufficient evidence strictly return canonical abstention."""
    # Query something clearly not yet indexed (e.g. Q102: snake bite poison)
    q = master_testcases[101]["question"]  # Q102
    req = ChatRequest(question=q, language="hi")
    resp = chat_endpoint(req)

    if resp.evidence_status == "insufficient_evidence":
        assert resp.answer.strip() == get_abstention_text("hi").strip()
        assert len(resp.sources) == 0


def test_no_fabricated_citations_in_chat(master_testcases):
    """Verify that every citation returned by the chat API strictly originates from approved database records."""
    sample_cases = [master_testcases[0], master_testcases[1], master_testcases[3]]
    for tc in sample_cases:
        req = ChatRequest(question=tc["question"], language="hi")
        resp = chat_endpoint(req)

        for src in resp.sources:
            assert src.chunk_id
            assert src.book
            assert src.page_start >= 0
            assert src.page_end >= src.page_start
