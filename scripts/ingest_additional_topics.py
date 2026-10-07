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
    {
        "id": "TOPIC_GAYATRI_DARSHAN_03",
        "section": "Darshan & Divine Realization (माँ गायत्री का सुलभ दर्शन एवं साक्षात्कार)",
        "question": "How to get darshan of lord Gayatri (माँ गायत्री का दर्शन एवं साक्षात्कार कैसे प्राप्त करें)?",
        "question_hi": "गायत्री माता का दर्शन एवं साक्षात्कार कैसे प्राप्त करें?",
        "content": (
            "Scripture / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "Theme / Subject: Darshan & Divine Realization (माँ गायत्री का सुलभ दर्शन एवं साक्षात्कार)\n"
            "Question / Query: How to get darshan of lord Gayatri (divine vision, realization, or inner communion of Mother Gayatri)?\n"
            "Authorized Spiritual Guidance: In Gayatri Mahavigyan, obtaining the Darshan (divine vision, realization, or inner communion) of Mother Gayatri "
            "is described by Pandit Shriram Sharma Acharya as a systematic, spiritual science of inner purification and meditation:\n"
            "1. Understanding Her True Nature: Gayatri is not merely an external physical deity, but the primordial cosmic energy (Aadya-Shakti), divine light "
            "(Brahma-Tej), and righteous intellect residing within the inner self (Antahkaran). Therefore, Her Darshan is both an inner realization of the divine "
            "soul-light and a direct connection with Her subtle presence.\n"
            "2. Purification of the Inner Self (Manobhoomi Shuddhi): Just as a clean, polished mirror clearly reflects a face while a dirty mirror hides it, the mind "
            "must be cleansed of ego, greed, and negative desires. As Satoguna (purity) increases through regular Sadhana, the dark layer covering the soul dissolves, "
            "allowing the divine light of Mother Gayatri to manifest clearly.\n"
            "3. Forms in Which Darshan Manifests: Luminous Light (Jyoti Roop) as a radiant flame in the heart center or eyebrow center (Triputi); Visual Form (Sakar Roop) "
            "seeing Mother Gayatri (such as Hansvahini, seated on a lotus) during deep meditation (Dhyan), dreams (Swapna), or waking consciousness; Divine Inner Voice "
            "(Vartalaap) receiving clear inner inspiration and intuitive wisdom within a quieted mind; Self-Realization (Aatma-Darshan) realizing the divine spark of God within one's soul.\n"
            "4. Practical Meditation Technique for Seeking Her Darshan: Sit comfortably in a quiet, clean space; close eyes and meditate on Gayatri Shakti at the heart center "
            "— either as radiant light (Jyoti) or Her visual form (Hansvahini) — feeling Her presence for about 10 minutes; take three slow deep breaths contemplating cosmic divine energy "
            "entering every cell; enter thoughtless stillness (Vichar-Shoonya) releasing mental images; in this quietude, a subtle inner impulse (Sphurana) arises spontaneously granting guidance and peace.\n"
            "5. Essential Mindset: Seeking Her Darshan requires unselfish devotion, faith, and a focus on spiritual growth, self-transformation, and noble service rather than material greed.\n"
            "Core Spiritual Concepts: how to get darshan of lord gayatri, darshan of gayatri, gayatri darshan, gayatri sakshatkar, divine vision of gayatri, communion with gayatri, aadya shakti, brahma tej, manobhoomi shuddhi, jyoti roop, sakar roop, hansvahini, vichar-shoonya, sphurana, aatma darshan\n"
        ),
        "page": 173,
    },
    {
        "id": "TOPIC_GAYATRI_DARSHAN_HI_04",
        "section": "माँ गायत्री का सुलभ दर्शन एवं साक्षात्कार साधना",
        "question": "माँ गायत्री का दर्शन और साक्षात्कार कैसे प्राप्त करें?",
        "question_hi": "गायत्री माता का दर्शन एवं साक्षात्कार कैसे प्राप्त करें?",
        "content": (
            "ग्रन्थ / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "विषय / Subject: माँ गायत्री का सुलभ दर्शन एवं साक्षात्कार (Darshan of Mother Gayatri)\n"
            "जिज्ञासा / Question: माँ गायत्री का दर्शन और साक्षात्कार कैसे प्राप्त करें (How to get darshan of lord Gayatri)?\n"
            "प्रमाणिक आध्यात्मिक मार्गदर्शन: पूज्य गुरुदेव पं. श्रीराम शर्मा आचार्य जी ने गायत्री महाविज्ञान में स्पष्ट किया है कि गायत्री कोई स्वतंत्र भौतिक देवी-देवता नहीं हैं, "
            "बल्कि परब्रह्म परमात्मा की क्रियाशील आद्याशक्ति, ब्रह्म-तेज और अंतःकरण में प्रतिष्ठित सद्बुद्धि हैं। गायत्री का दर्शन अंतःकरण में भगवती चेतना के साक्षात्कार का विज्ञान है:\n"
            "१. मनोभूमि की शुद्धि: जिस प्रकार स्वच्छ शीशे में ही अपना मुख स्पष्ट दिखता है, उसी प्रकार वासनाओं, अहंकार और लोभ से मुक्त निर्मल अंतःकरण में ही माँ गायत्री का प्रकाश झलकता है। "
            "साधना से सतोगुण की वृद्धि होने पर मलिनता हटती है और दिव्य दर्शन सुलभ होता है।\n"
            "२. दर्शन के मुख्य स्वरूप: ज्योति रूप (हृदय या भ्रूमध्य में ज्योतिर्मय प्रकाश का अनुभव), साकार रूप (कमल पर विराजमान हंसवाहिनी माँ का ध्यान या स्वप्न में दर्शन), अंतर्वाणी (शांत चित्त में सत्प्रेरणा व मार्गदर्शन), आत्मदर्शन (स्वयं की आत्मा में परमात्मा की उपस्थिति का साक्षात्कार)।\n"
            "३. सुलभ ध्यान-साधना विधि: पवित्र भाव से बैठकर हृदय में माँ गायत्री के ज्योति स्वरूप या हंसवाहिनी रूप का १० मिनट ध्यान करें; तीन प्राणायाम द्वारा ब्रह्माण्डीय प्राण-शक्ति का आकर्षण करें; फिर मन को पूर्णतः विचार-शून्य (निर्विकल्प) कर दें। इस शांत अवस्था में जो स्फुरणा (दिव्य प्रेरणा) उठती है, वही माँ गायत्री का प्रत्यक्ष मार्गदर्शन व साक्षात्कार है।\n"
            "४. आवश्यक दृष्टिकोण: निष्काम भक्ति, सेवाभाव और आत्म-परिष्कार ही दर्शन का मूल आधार है।\n"
            "मुख्य पारिभाषिक शब्द: गायत्री दर्शन, माँ गायत्री का दर्शन, Gayatri Darshan, how to get darshan of lord gayatri, साक्षात्कार, सुलभ दर्शन, ज्योति रूप, हंसवाहिनी, मनोभूमि शुद्धि, विचार-शून्य, स्फुरणा, आत्मदर्शन\n"
        ),
        "page": 174,
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
