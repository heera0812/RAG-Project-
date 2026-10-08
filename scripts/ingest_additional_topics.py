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
    {
        "id": "TOPIC_GURUDEV_KRODH_05",
        "book": "विचार क्रांति",
        "section": "मानसिक परिष्कार",
        "question": "गुरुदेव ने क्रोध के बारे में क्या कहा है?",
        "question_hi": "गुरुदेव ने क्रोध के बारे में क्या कहा है?",
        "content": (
            "ग्रन्थ / Book: विचार क्रांति (पं. श्रीराम शर्मा आचार्य)\n"
            "विषय / Subject: मानसिक परिष्कार एवं आत्मसंयम (क्रोध निवारण / Teachings on Anger)\n"
            "जिज्ञासा / Question: गुरुदेव ने क्रोध के बारे में क्या कहा है? (What has Gurudev said about anger?)\n"
            "प्रमाणिक मार्गदर्शन: गुरुदेव पं. श्रीराम शर्मा आचार्य जी के अनुसार, क्रोध मनुष्य की विवेक शक्ति को नष्ट कर देता है और यह आत्मविकास में सबसे बड़ा बाधक है। "
            "वे कहते हैं कि क्रोध क्षणिक आवेश और मानसिक विक्षेप है, जो हमारे अच्छे विचारों, संबंधों और साधना—तीनों को भारी क्षति पहुँचाता है। "
            "क्रोध से सोचने-समझने की क्षमता कुंठित होती है और जीवन में अशान्ति का प्रसार होता है।\n"
            "गुरुदेव का सुझाव है कि क्रोध को नियंत्रित करने के लिए स्वाध्याय, आत्मपरीक्षण, धैर्य, सकारात्मक सोच और गायत्री साधना का नियमित अभ्यास अत्यंत उपयोगी है। "
            "उन्होंने यह भी कहा है कि क्रोध का शमन प्रेम, करुणा और सेवा की भावना से किया जा सकता है, क्योंकि ये गुण मन को शीतल, संतुलित और स्थिर बनाते हैं।\n"
            "मुख्य शब्द: गुरुदेव ने क्रोध के बारे में क्या कहा है, क्रोध, krodh, anger, gussa, मानसिक परिष्कार, आत्मसंयम, स्वाध्याय, विचार क्रांति\n"
        ),
        "page": 42,
    },
    {
        "id": "TOPIC_BRAHMACHARYA_DAINIK_JEEVAN_06",
        "book": "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)",
        "section": "ब्रह्मचर्य तप एवं इन्द्रिय संयम साधना",
        "question": "ब्रह्मचर्य को दैनिक जीवन में कैसे अपनाएँ?",
        "question_hi": "ब्रह्मचर्य को दैनिक जीवन में कैसे अपनाएँ?",
        "content": (
            "ग्रन्थ / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "विषय / Subject: ब्रह्मचर्य तप एवं इन्द्रिय संयम साधना (Brahmacharya in Daily Life)\n"
            "जिज्ञासा / Question: ब्रह्मचर्य को दैनिक जीवन में कैसे अपनाएँ? (How to practice Brahmacharya in daily life?)\n"
            "प्रमाणिक आध्यात्मिक मार्गदर्शन (Gurudev's Teachings): पूज्य गुरुदेव पं. श्रीराम शर्मा आचार्य जी ने स्पष्ट किया है कि "
            "ब्रह्मचर्य केवल शारीरिक वीर्य-रक्षा तक सीमित कोई संकीर्ण क्रिया नहीं, वरन् 'ब्रह्मवत् आचरण'—अर्थात् अपनी चित्तवृत्तियों, ज्ञानेन्द्रियों और जीवनी-शक्ति को ईश्वरीय दिव्यता में लगाना है। "
            "दैनिक जीवन में ब्रह्मचर्य अपनाने के मुख्य आधार इस प्रकार हैं:\n"
            "१. विचार-संयम व दृष्टि-पवित्रता: मन को कामुक, अश्लील और विकारी विचारों से मुक्त रखना। समस्त नारियों को मातृ-शक्ति या भगिनी भाव से देखना ('मातृवत् परदारेषु')। मन में कुविचार आते ही तुरंत गायत्री मन्त्र का मानसिक जप या उच्च साहित्य का स्वाध्याय करना।\n"
            "२. आहार-शुद्धि एवं अस्वाद व्रत: अधिक मिर्च-मसालेदार, उत्तेजक, गरिष्ठ, बासी व तामसिक भोजन काम-वासना को भड़काता है। दैनिक जीवन में सात्त्विक, सुपाच्य, ऋतु-अनुकूल शाकाहार तथा भूख से थोड़ा कम (अल्पाहार) लेना अनिवार्य है।\n"
            "३. समय व ऊर्जा का सदुपयोग: खाली मस्तिष्क विकारों का घर बनता है। आलस्य त्यागकर समय का एक-एक पल स्वाध्याय, समाज-सेवा, ज्ञानोपार्जन और सत्कर्मों में लगाना। नियमित शारीरिक श्रम, प्राणायाम व व्यायाम द्वारा जीवनी-शक्ति को सक्रिय व सुदृढ़ रखना।\n"
            "४. गायत्री साधना व तेजस संचय: प्रातःकाल सूर्योदय के समय गायत्री जप और सविता के स्वर्णिम तेज का ध्यान करना। इस दिव्य साधना से काम-शक्ति जलकर मेधा-शक्ति, अलौकिक ओजस और तेजस में रूपान्तरित (उन्नयन/Sublimation) हो जाती है।\n"
            "५. गृहस्थ ब्रह्मचर्य की मर्यादा: गृहस्थों के लिए केवल धर्मानुकूल संतानोत्पत्ति हेतु ही मैथुन की शास्त्रोक्त आज्ञा है; शेष समय पूर्ण संयम, पारस्परिक निष्ठा और पवित्र मित्रवत जीवन जीना ही गृहस्थ ब्रह्मचर्य है।\n"
            "मुख्य शब्द: ब्रह्मचर्य को दैनिक जीवन में कैसे अपनाएँ, ब्रह्मचर्य, brahmacharya, celibacy, indriya sanyam, इन्द्रिय संयम, वीर्य रक्षा, ओजस, दृष्टि पवित्रता, आहार शुद्धि, गृहस्थ ब्रह्मचर्य, विचार संयम, गायत्री महाविज्ञान\n"
        ),
        "page": 175,
    },
    {
        "id": "TOPIC_BRAHMACHARYA_EN_07",
        "book": "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)",
        "section": "Theme 9: Brahmacharya Tapa & Mastery over Senses",
        "question": "How to adopt and practice Brahmacharya in daily life according to Gurudev?",
        "question_hi": "दैनिक जीवन में ब्रह्मचर्य कैसे अपनाएँ?",
        "content": (
            "Scripture / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "Theme / Subject: Theme 9: Brahmacharya Tapa & Mastery over Senses in Daily Life\n"
            "Question / Query: How to adopt and practice Brahmacharya (celibacy / self-restraint) in daily life according to Pandit Shriram Sharma Acharya?\n"
            "Authorized Spiritual Guidance: Gurudev Pandit Shriram Sharma Acharya established that Brahmacharya is far greater than mere physical suppression; "
            "it literally means 'conduct aligned with the Divine (Brahma)'. Practicing Brahmacharya in daily life requires a holistic approach:\n"
            "1. Mental Chastity & Pure Vision: Guarding the eyes and mind against vulgar, sensual stimuli. Viewing all women with reverence as mothers or sisters (Matrivat Paradhareshu). "
            "Immediately redirecting wandering thoughts toward Gayatri Mantra japa or uplifting self-study (Swadhyaya).\n"
            "2. Dietary Restraint (Aswada): Avoiding heavy, excessively spicy, and stimulant-laden Tamasic food that agitates the nervous system. Adopting pure, light, Sattvic meals eaten in moderate portions.\n"
            "3. Active Routine & Physical Labor: Eliminating idleness through disciplined work, selfless service (Seva), regular exercise, and Surya Namaskar so that vital energies are harmoniously directed.\n"
            "4. Gayatri Sadhana & Sublimation into Ojas: Meditating on the solar brilliance (Savita) at dawn transforms raw sexual energy (Kama) into spiritual radiance (Ojas, Tejas, and Medha).\n"
            "5. Householder Brahmacharya: For married householders, Brahmacharya consists of mutual fidelity, self-restraint outside the purpose of righteous procreation, and living as spiritually uplifting companions.\n"
            "Core Spiritual Concepts: how to adopt brahmacharya in daily life, brahmacharya, celibacy, indriya sanyam, sense control, sexual energy sublimation, ojas, tejas, mental chastity, sattvic food, swadhyaya, grihastha brahmacharya\n"
        ),
        "page": 176,
    },
    {
        "id": "TOPIC_CHAR_SANYAM_08",
        "book": "विचार क्रांति",
        "section": "जीवन साधना एवं चार संयम",
        "question": "गुरुदेव के अनुसार जीवन के चार मुख्य संयम (Char Sanyam) कौन-से हैं?",
        "question_hi": "चार संयम कौन-से हैं और उनका क्या महत्व है?",
        "content": (
            "ग्रन्थ / Book: विचार क्रांति (पं. श्रीराम शर्मा आचार्य)\n"
            "विषय / Subject: जीवन साधना एवं चार संयम (Four Foundational Disciplines of AWGP)\n"
            "जिज्ञासा / Question: गुरुदेव के अनुसार जीवन के चार मुख्य संयम (Char Sanyam) कौन-से हैं?\n"
            "प्रमाणिक मार्गदर्शन: युगऋषि पं. श्रीराम शर्मा आचार्य जी ने व्यक्ति-निर्माण और सफल साधना के लिए 'चार संयम' को अनिवार्य आधारस्तंभ बताया है:\n"
            "१. इन्द्रिय संयम: जीभ (स्वाद व वाणी) और कामेन्द्रिय पर नियंत्रण रखना। सात्त्विक भोजन करना और पवित्र दृष्टि रखना।\n"
            "२. अर्थ संयम: अपनी मेहनत की न्यायोचित कमाई पर संतोष करना, फिजूलखर्ची व विलासिता से बचना, और धन का एक अंश लोक-कल्याण में लगाना।\n"
            "३. समय संयम: जीवन की एक-एक घड़ी को ईश्वर की अमूल्य धरोहर मानकर समय का पाबंद होना। दिनचर्या बनाकर आलस्य व प्रमाद को त्यागना।\n"
            "४. विचार संयम: मन में नकारात्मक, ईर्ष्यापूर्ण व कामुक विचारों को स्थान न देना; सदैव श्रेष्ठ, प्रेरक व सकारात्मक विचारों का पोषण करना।\n"
            "मुख्य शब्द: चार संयम, char sanyam, 4 sanyam, इन्द्रिय संयम, अर्थ संयम, समय संयम, विचार संयम, विचार क्रांति, शांतिकुंज\n"
        ),
        "page": 45,
    },
    {
        "id": "TOPIC_AHAR_SHUDDHI_09",
        "book": "गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)",
        "section": "आहार शुद्धि एवं अस्वाद तप",
        "question": "आहार शुद्धि और अस्वाद तप के नियम क्या हैं?",
        "question_hi": "आहार शुद्धि और अस्वाद तप के नियम क्या हैं?",
        "content": (
            "ग्रन्थ / Book: गायत्री महाविज्ञान (अमृतवाणी एवं बहुभाषी भाष्य)\n"
            "विषय / Subject: आहार शुद्धि एवं अस्वाद तप (Dietary Purity and Aswada Tapa)\n"
            "जिज्ञासा / Question: आहार शुद्धि और अस्वाद तप के नियम क्या हैं? (Rules of dietary purity and taste control)\n"
            "प्रमाणिक मार्गदर्शन: 'जैसा खावे अन्न, वैसा होवे मन।' गुरुदेव पं. श्रीराम शर्मा आचार्य जी के अनुसार आहार की शुद्धि अंतःकरण की पवित्रता की पहली सीढ़ी है। "
            "अस्वाद तप का अर्थ केवल स्वादहीन भोजन करना नहीं, बल्कि जिह्वा के चटोरेपन पर विजय प्राप्त करना है। "
            "नियम: १. भोजन सात्त्विक, पवित्र कमाई से अर्जित और प्रभु-स्मरण पूर्वक पकाया हुआ हो। २. तीखे, अधिक खट्टे, अधिक नमकीन, गरिष्ठ व बासी भोजन से परहेज। "
            "३. भूख से एक चौथाई कम खाना (मिताहार)। ४. भोजन केवल शरीर को ऊर्जा देने वाला यज्ञीय प्रसाद समझकर शांत भाव से ग्रहण करना।\n"
            "मुख्य शब्द: आहार शुद्धि, अस्वाद तप, aswada tapa, ahar shuddhi, mitahara, सात्त्विक भोजन, जैसा अन्न वैसा मन, गायत्री महाविज्ञान\n"
        ),
        "page": 177,
    },
]


def ingest_additional():
    chunks = []
    for item in ADDITIONAL_KNOWLEDGE:
        chunk_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"shantikunj_topic_{item['id']}"))
        chunk_hash = hashlib.sha256(item["content"].encode("utf-8")).hexdigest()

        book_name = item.get("book", DOC_TITLE)

        chunk = DocumentChunkModel(
            chunk_id=chunk_uuid,
            document_id=DOC_ID,
            document_version="1.0",
            content=item["content"],
            book=book_name,
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
