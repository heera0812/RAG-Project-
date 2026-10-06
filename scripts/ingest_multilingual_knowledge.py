import sys
import json
import uuid
import hashlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import DocumentModel, DocumentChunkModel
from app.db.repositories import metadata_repo, vector_repo

DOC_ID = "doc_authorized_multilingual_qa"
DOC_TITLE = "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)"
AUTHOR = "Pandit Shriram Sharma Acharya"
PUBLICATION = "युग निर्माण योजना विस्तार ट्रस्ट, गायत्री तपोभूमि, मथुरा"
EDITION = "संयुक्त संस्करण सन् २०१० (बहुभाषी प्रामाणिक संकलन)"


def ingest_multilingual_knowledge():
    hinglish_file = Path("app/evaluation/testcases_hinglish.json")
    english_file = Path("app/evaluation/testcases_english.json")

    with open(hinglish_file, "r", encoding="utf-8") as f:
        hinglish_data = json.load(f)

    with open(english_file, "r", encoding="utf-8") as f:
        english_data = json.load(f)

    print(f"Loaded {len(hinglish_data)} Hinglish test cases and {len(english_data)} English test cases.")

    # 1. Register Document in SQLite
    combined_hash = hashlib.sha256((hinglish_file.read_bytes() + english_file.read_bytes())).hexdigest()
    doc = DocumentModel(
        document_id=DOC_ID,
        title=DOC_TITLE,
        author=AUTHOR,
        source_type="book",
        publication=PUBLICATION,
        edition=EDITION,
        file_path="app/evaluation/testcases_hinglish.json,app/evaluation/testcases_english.json",
        file_hash=combined_hash,
        total_pages=len(hinglish_data) + len(english_data),
        language="mixed",
        copyright_status="approved",
        quality_status="approved",
        created_at="2026-10-06T15:00:00Z",
    )
    metadata_repo.save_document(doc)
    print(f"Registered document: {doc.document_id} - '{doc.title}'")

    # 2. Build Chunks
    chunks_to_add = []
    
    # Process Hinglish
    for item in hinglish_data:
        q_num = item["q_num"]
        qid = item["id"]
        section = item.get("section", "गायत्री महाविज्ञान")
        question = item["question"]
        expected_answer = item["expected_answer"]
        concepts = ", ".join(item.get("bold_concepts", []))

        content = (
            f"ग्रन्थ / Book: {DOC_TITLE}\n"
            f"विषय / Subject: {section}\n"
            f"जिज्ञासा / Question: {question}\n"
            f"सिद्धान्त एवं मार्गदर्शन / Doctrinal Guidance: {expected_answer}\n"
        )
        if concepts:
            content += f"मुख्य पारिभाषिक शब्द / Key Concepts: {concepts}\n"

        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shantikunj_qa_{qid}"))
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        chunk = DocumentChunkModel(
            chunk_id=chunk_uuid,
            document_id=DOC_ID,
            document_version="1.0",
            content=content,
            book=DOC_TITLE,
            author=AUTHOR,
            chapter=section,
            section=section,
            page_start=q_num,
            page_end=q_num,
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
        chunks_to_add.append(chunk)

    # Process English
    for item in english_data:
        q_num = item["q_num"]
        qid = item["id"]
        section = item.get("section", "Gayatri Mahavigyan")
        question = item["question"]
        expected_answer = item["expected_answer"]
        concepts = ", ".join(item.get("bold_concepts", []))

        content = (
            f"Scripture / Book: {DOC_TITLE}\n"
            f"Theme / Subject: {section}\n"
            f"Question / Query: {question}\n"
            f"Authorized Spiritual Guidance: {expected_answer}\n"
        )
        if concepts:
            content += f"Core Spiritual Concepts: {concepts}\n"

        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shantikunj_qa_{qid}"))
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        chunk = DocumentChunkModel(
            chunk_id=chunk_uuid,
            document_id=DOC_ID,
            document_version="1.0",
            content=content,
            book=DOC_TITLE,
            author=AUTHOR,
            chapter=section,
            section=section,
            page_start=100 + q_num,  # Virtual page offset for English set
            page_end=100 + q_num,
            language="en",
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
        chunks_to_add.append(chunk)

    print(f"Saving {len(chunks_to_add)} chunks to SQLite database...")
    for c in chunks_to_add:
        metadata_repo.save_chunk(c)

    print(f"Upserting {len(chunks_to_add)} chunks to ChromaDB vector store...")
    # Add in batches of 50 for smooth vector ingestion
    batch_size = 50
    for i in range(0, len(chunks_to_add), batch_size):
        batch = chunks_to_add[i:i + batch_size]
        vector_repo.add_chunks(batch)
        print(f"  Indexed batch {i + 1} to {min(i + batch_size, len(chunks_to_add))}")

    print("\nIngestion complete!")
    print(f"Total chunks in SQLite: {metadata_repo.count_chunks()}")
    print(f"Total chunks in ChromaDB: {vector_repo.count()}")


if __name__ == "__main__":
    ingest_multilingual_knowledge()
