from app.ingestion.quality_checks import QualityChecker
from app.db.models import DocumentChunkModel


def test_quality_check_page_valid():
    text = (
        "वेद कहते हैं-ज्ञान को। ज्ञान के चार भेद हैं-ऋक्, यजुः, साम और अथर्व। "
        "कल्याण, प्रभु-प्राप्ति, ईश्वरीय-दर्शन, दिव्यत्व, आत्म-शान्ति, धर्म-भावना, सेवा आदि ऋक् के अन्तर्गत आते हैं।"
    )
    is_valid, reason = QualityChecker.check_page_text(text)
    assert is_valid is True
    assert reason is None


def test_quality_check_page_empty():
    is_valid, reason = QualityChecker.check_page_text("   ")
    assert is_valid is False
    assert "Empty" in reason


def test_quality_check_page_garbage():
    garbage_text = "वेद ^~`_§±×÷¶†‡^~`_§±×÷¶†‡" * 5
    is_valid, reason = QualityChecker.check_page_text(garbage_text)
    assert is_valid is False
    assert "garbage" in reason or "Short" in reason or "Devanagari" in reason


def test_quality_check_chunk_valid():
    chunk = DocumentChunkModel(
        chunk_id="chk-123",
        document_id="doc-456",
        content="वेद कहते हैं-ज्ञान को। ज्ञान के चार भेद हैं-ऋक्, यजुः, साम और अथर्व। " * 3,
        book="गायत्री महाविज्ञान",
        page_start=1,
        page_end=1,
        content_hash="abc",
    )
    is_valid, reason = QualityChecker.check_chunk(chunk)
    assert is_valid is True


def test_quality_check_chunk_invalid_page_range():
    chunk = DocumentChunkModel(
        chunk_id="chk-123",
        document_id="doc-456",
        content="वेद कहते हैं-ज्ञान को। ज्ञान के चार भेद हैं-ऋक्, यजुः, साम और अथर्व। " * 3,
        book="गायत्री महाविज्ञान",
        page_start=5,
        page_end=3,  # Invalid: start > end
        content_hash="abc",
    )
    is_valid, reason = QualityChecker.check_chunk(chunk)
    assert is_valid is False
    assert "Invalid page range" in reason
