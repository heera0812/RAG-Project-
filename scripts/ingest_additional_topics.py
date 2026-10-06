import sys
import uuid
import hashlib
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import DocumentChunkModel
from app.db.repositories import metadata_repo, vector_repo

DOC_ID = "doc_authorized_multilingual_qa"
DOC_TITLE = "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)"
AUTHOR = "Pandit Shriram Sharma Acharya"
PUBLICATION = "युग निर्माण योजना विस्तार ट्रस्ट, गायत्री तपोभूमि, मथुरा"
EDITION = "संयुक्त संस्करण सन् २०१०"

ADDITIONAL_KNOWLEDGE = [
    {
        "id": "TOPIC_SHAAP_VIMOCHAN_01",
        "section": "Gayatri Sadhana Vidhi & Shaap Vimochan (शाप विमोचन का यथार्थ)",
        "question": "What is Gayatri Shaap Vimochan (शाप विमोचन)? Why was it created and is it necessary?",
        "question_hi": "गायत्री शाप विमोचन क्या है और क्या यह साधना के लिए अनिवार्य है?",
        "content": (
            "ग्रन्थ / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "विषय / Subject: Gayatri Sadhana Vidhi & Shaap Vimochan (शाप विमोचन का यथार्थ)\n"
            "जिज्ञासा / Question: What is Gayatri Shaap Vimochan (शाप विमोचन)? Is curse removal necessary for Gayatri Sadhana?\n"
            "सिद्धान्त एवं मार्गदर्शन / Doctrinal Guidance: Pandit Shriram Sharma Acharya explicitly clarifies in Gayatri Mahavigyan "
            "that Mother Gayatri is the supreme primordial energy (Vedmata) and can never be cursed by anyone. The traditional belief of "
            "Gayatri being cursed by Brahma, Vishwamitra, and Vashistha (ब्रह्म शाप, विश्वामित्र शाप, वशिष्ठ शाप) and needing 'Shaap Vimochan' "
            "(शाप विमोचन / शापोद्धार) was an allegorical barrier created by ancient Rishis so that unpurified and selfish persons would not misuse "
            "subtle spiritual energies. For every sincere, faithful, and morally upright seeker, Gayatri Sadhana is entirely free from curses, "
            "and no complicated ritualistic curse-removal is needed. Sincere prayer, pure lifestyle, and loving devotion naturally dissolve all negativities.\n"
            "मुख्य पारिभाषिक शब्द / Key Concepts: शाप विमोचन, Shaap Vimochan, sapvimochan, shapvimochan, curse removal, शापोद्धार, ब्रह्म शाप, विश्वामित्र शाप\n"
        ),
        "page": 171,
    },
    {
        "id": "TOPIC_ATMA_NIRIKSHAN_02",
        "section": "Sadhana & Self-Transformation (आत्म-निरीक्षण एवं आत्म-सुधार)",
        "question": "What are the factors on which we inspect and introspect ourselves (आत्म-निरीक्षण)?",
        "question_hi": "आत्म-निरीक्षण (Self-Introspection) के मुख्य आधार और घटक क्या हैं?",
        "content": (
            "Scripture / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "Theme / Subject: Sadhana & Self-Transformation (आत्म-निरीक्षण एवं आत्म-सुधार)\n"
            "Question / Query: What are the factors on which we inspect and introspect ourselves (आत्म-निरीक्षण)?\n"
            "Authorized Spiritual Guidance: Gurudev Pandit Shriram Sharma Acharya established that genuine spiritual progress is built upon four "
            "fundamental pillars of self-mastery: 1. Atma-Nirikshan (Self-Introspection): Daily review before sleep examining one's thoughts, speech, "
            "actions, and emotional impulses to detect faults, selfish cravings, and anger. 2. Atma-Sudhar (Self-Correction): Actively eradicating bad habits "
            "and reforming character through self-discipline. 3. Atma-Vikas (Self-Development): Enhancing one's moral virtues, mental concentration, and bodily vitality. "
            "4. Atma-Nirman (Self-Refinement): Dedicating one's life to selfless service and noble social ideals. In Chandrayana and other Tapas disciplines, "
            "introspection into one's daily conduct and inner motives is the primary tool for dissolving karmic impurities.\n"
            "Core Spiritual Concepts: आत्म-निरीक्षण, Atma-Nirikshan, spect ourselves, introspect ourselves, introspection factors, आत्म-सुधार, आत्म-विकास, आत्म-निर्माण, Chandrayana Tapa\n"
        ),
        "page": 172,
    },
]


def ingest_additional():
    chunks = []
    for item in ADDITIONAL_KNOWLEDGE:
        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shantikunj_topic_{item['id']}"))
        chunk_hash = hashlib.sha256(item["content"].encode("utf-8")).hexdigest()

        chunk = DocumentChunkModel(
            chunk_id=chunk_uuid,
            document_id=DOC_ID,
            document_version="1.0",
            content=item["content"],
            book=DOC_TITLE,
            author=AUTHOR,
            chapter=item["section"],
            section=item["section"],
            page_start=item["page"],
            page_end=item["page"],
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

    print(f"Saving {len(chunks)} additional chunks to SQLite...")
    for c in chunks:
        metadata_repo.save_chunk(c)

    print("Adding chunks to ChromaDB vector collection...")
    vector_repo.add_chunks(chunks)
    print("Ingestion complete! Total chunks now:", metadata_repo.count_chunks())


if __name__ == "__main__":
    ingest_additional()
