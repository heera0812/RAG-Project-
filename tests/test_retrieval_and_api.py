from fastapi.testclient import TestClient
from app.main import app
from app.retrieval.query_normalizer import query_normalizer
from app.generation.abstention import get_abstention_text

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_query_normalizer_hinglish():
    query = "gussa kaise control karein?"
    expanded, matched, lang = query_normalizer.normalize_query(query)
    assert "gussa" in matched
    assert "क्रोध" in expanded or "गुस्सा" in expanded


def test_abstention_text():
    hi_text = get_abstention_text("hi")
    en_text = get_abstention_text("en")
    assert "पर्याप्त आधार नहीं मिला" in hi_text
    assert "sufficient supporting material" in en_text


def test_chat_abstention_when_unanswerable():
    # Chat with out-of-domain query should abstain safely
    response = client.post(
        "/api/chat",
        json={"question": "What is the stock price of Apple on NASDAQ today?", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["evidence_status"] == "insufficient_evidence"
    assert len(data["sources"]) == 0
    assert "sufficient supporting material" in data["answer"]
