"""Tests to verify the 19 difficult test cases from Agent.md/master rule/difficult test case."""
import json
from pathlib import Path
import pytest
from app.retrieval.hybrid_search import hybrid_search_engine
from app.generation.answer_generator import answer_generator


@pytest.fixture(scope="module")
def difficult_cases():
    json_path = Path("app/evaluation/difficult_testcases.json")
    if not json_path.exists():
        from scripts.export_difficult_testcases import parse_and_export_difficult_testcases
        parse_and_export_difficult_testcases()

    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    return cases


def test_difficult_dataset_loaded(difficult_cases):
    """Ensure dataset contains valid items covering hi, en, and hinglish."""
    assert len(difficult_cases) >= 50
    langs = {c["language"] for c in difficult_cases}
    assert "hi" in langs
    assert "en" in langs
    assert "hinglish" in langs


@pytest.mark.parametrize("query,expected_keyword", [
    ("Why does taking unearned donations/gifts (Pratigraha) not corrupt a dedicated Gayatri practitioner?", "बृहदारण्यक"),
    ("Gayatri sadhak jab koi unearned gift/donation (Pratigraha) leta hai toh use paap kyu nahi lagta?", "Brihadaranyaka"),
    ("What are the assigned mantra portions and visualizations for the 4 stages of Gayatri Pranayama (Puraka, Antah-Kumbhaka, Rechaka, Bahya-Kumbhaka)?", "Puraka"),
    ("What is the scriptural specification for the three forms during Trikal Sandhya?", "Brahmi"),
    ("Why are the 9 threads of the Yagyopaveet compared to a Naulakha Haar?", "Naulakha"),
])
def test_difficult_retrieval_matches(query, expected_keyword):
    """Verify that hybrid search surfaces appropriate chunks for difficult queries."""
    results, confidence = hybrid_search_engine.search(query=query, top_k=3, use_hybrid=True)
    assert len(results) > 0
    assert confidence in ("high", "medium")
    combined_text = " ".join([r.content for r in results])
    assert expected_keyword.lower() in combined_text.lower()
