from app.db.models import DocumentPageModel
from app.ingestion.chunker import StructureAwareChunker


def test_structure_aware_chunker():
    chunker = StructureAwareChunker(target_chars=300, overlap_chars=50)

    pages = [
        DocumentPageModel(
            page_id="p1",
            document_id="doc-1",
            pdf_page_index=10,
            printed_page_number=1,
            raw_text="१. वेदमाता गायत्री की उत्पत्ति\n\nवेद कहते हैं-ज्ञान को। ज्ञान के चार भेद हैं।",
            cleaned_text="१. वेदमाता गायत्री की उत्पत्ति\n\nवेद कहते हैं-ज्ञान को। ज्ञान के चार भेद हैं।",
        ),
        DocumentPageModel(
            page_id="p2",
            document_id="doc-1",
            pdf_page_index=11,
            printed_page_number=2,
            raw_text="कल्याण, प्रभु-प्राप्ति ऋक् के अन्तर्गत आते हैं।",
            cleaned_text="कल्याण, प्रभु-प्राप्ति ऋक् के अन्तर्गत आते हैं।",
        ),
    ]

    chunks = chunker.chunk_pages(
        pages=pages,
        document_id="doc-1",
        book_title="गायत्री महाविज्ञान",
    )

    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert first_chunk.document_id == "doc-1"
    assert first_chunk.book == "गायत्री महाविज्ञान"
    assert first_chunk.page_start >= 1
    assert first_chunk.content_hash != ""
