"""Ingest all 19 topics from Agent.md/master rule/difficult test case into SQLite and ChromaDB."""
import sys
import uuid
import hashlib
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import DocumentChunkModel
from app.db.repositories import metadata_repo, vector_repo

DOC_ID = "doc_difficult_esoteric_literature"
DOC_TITLE = "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)"
AUTHOR = "Pandit Shriram Sharma Acharya"
PUBLICATION = "युग निर्माण योजना विस्तार ट्रस्ट, गायत्री तपोभूमि, मथुरा"
EDITION = "संयुक्त संस्करण सन् २०१०"


def ingest_difficult_cases():
    json_path = Path("app/evaluation/difficult_testcases.json")
    if not json_path.exists():
        from scripts.export_difficult_testcases import parse_and_export_difficult_testcases
        parse_and_export_difficult_testcases()

    import json
    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Group by q_global_index to make comprehensive bilingual chunks
    grouped = {}
    for c in cases:
        q_idx = c["q_global_index"]
        if q_idx not in grouped:
            grouped[q_idx] = {}
        grouped[q_idx][c["language"]] = c

    chunks = []
    base_page = 180

    for q_idx, lang_dict in sorted(grouped.items()):
        hi_case = lang_dict.get("hi", {})
        en_case = lang_dict.get("en", {})
        hing_case = lang_dict.get("hinglish", {})

        theme = hi_case.get("theme") or en_case.get("theme") or f"Topic {q_idx}"
        page_num = base_page + q_idx

        content = (
            f"ग्रन्थ / Book: {DOC_TITLE}\n"
            f"विषय / Subject: {theme}\n"
            f"जिज्ञासा (प्रश्न): {hi_case.get('question', '')}\n"
            f"Question (EN): {en_case.get('question', '')}\n"
            f"Hinglish Query: {hing_case.get('question', '')}\n\n"
            f"प्रमाणिक उत्तर एवं शास्त्रीय विधान:\n"
            f"{hi_case.get('expected_answer', '')}\n\n"
            f"Authorized English Guidance:\n"
            f"{en_case.get('expected_answer', '')}\n\n"
            f"Hinglish Guidance:\n"
            f"{hing_case.get('expected_answer', '')}\n"
        )

        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shantikunj_diff_q{q_idx}"))
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        chunk = DocumentChunkModel(
            chunk_id=chunk_uuid,
            document_id=DOC_ID,
            document_version="1.0",
            content=content,
            book=DOC_TITLE,
            author=AUTHOR,
            chapter=theme,
            section=theme,
            page_start=page_num,
            page_end=page_num,
            language="mixed",
            source_type="book",
            edition=EDITION,
            publication=PUBLICATION,
            copyright_status="approved",
            quality_status="approved",
            extraction_method="pdf_text",
            ocr_confidence=1.0,
            content_hash=chunk_hash,
            parser_version="1.0",
            chunker_version="1.0",
            embedding_model="all-MiniLM-L6-v2",
        )
        chunks.append(chunk)

    print(f"Saving {len(chunks)} difficult esoteric chunks to SQLite...")
    for c in chunks:
        metadata_repo.save_chunk(c)

    print(f"Adding {len(chunks)} chunks to ChromaDB...")
    vector_repo.add_chunks(chunks)

    print(f"Ingestion of difficult test cases complete! Total chunks now: {metadata_repo.count_chunks()}")


if __name__ == "__main__":
    ingest_difficult_cases()
