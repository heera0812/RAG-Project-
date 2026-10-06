from app.db.models import SearchResultItem
from app.generation.citation_validator import CitationValidator


def test_citation_validator_valid():
    validator = CitationValidator()
    item = SearchResultItem(
        chunk_id="chunk-valid-1",
        document_id="doc-1",
        content="वेद कहते हैं ज्ञान को।",
        score=0.88,
        metadata={
            "book": "गायत्री महाविज्ञान",
            "chapter": "वेदमाता गायत्री की उत्पत्ति",
            "page_start": 1,
            "page_end": 2,
            "source_type": "book",
        },
    )

    claimed_ids = ["chunk-valid-1"]
    validated, is_valid = validator.validate_citations(claimed_ids, [item])

    assert is_valid is True
    assert len(validated) == 1
    assert validated[0].chunk_id == "chunk-valid-1"
    assert validated[0].book == "गायत्री महाविज्ञान"
    assert validated[0].page_start == 1
    assert validated[0].page_end == 2


def test_citation_validator_fabricated():
    validator = CitationValidator()
    item = SearchResultItem(
        chunk_id="chunk-valid-1",
        document_id="doc-1",
        content="वेद कहते हैं ज्ञान को।",
        score=0.88,
        metadata={
            "book": "गायत्री महाविज्ञान",
            "page_start": 1,
            "page_end": 1,
        },
    )

    claimed_ids = ["fabricated-chunk-id-999"]
    validated, is_valid = validator.validate_citations(claimed_ids, [item])

    assert is_valid is False
    assert len(validated) == 0
