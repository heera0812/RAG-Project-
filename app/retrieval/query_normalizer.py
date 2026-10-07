import re
from typing import List, Dict, Tuple
from app.ingestion.language import detect_language

# Term glossary supporting Hindi, Hinglish, and English queries
TERM_GLOSSARY: Dict[str, List[str]] = {
    # Emotional & Psychological
    "gussa": ["गुस्सा", "क्रोध", "krodh", "anger"],
    "krodh": ["क्रोध", "गुस्सा"],
    "anger": ["क्रोध", "गुस्सा"],
    "self control": ["आत्मसंयम", "संयम", "manonigrah", "मनोनिग्रह"],
    "sanyam": ["संयम", "आत्मसंयम"],
    "meditation": ["ध्यान", "साधना", "उपासना"],
    "dhyan": ["ध्यान", "उपासना"],
    "sadhana": ["साधना", "उपासना", "तप"],
    "discipline": ["अनुशासन", "संयम", "आत्मसंयम"],
    "anushasan": ["अनुशासन", "संयम"],
    "brahmacharya": ["ब्रह्मचर्य", "इन्द्रिय संयम"],
    "celibacy": ["ब्रह्मचर्य"],
    "aatma-kalyan": ["आत्म-कल्याण", "ब्रह्म-ज्ञान"],
    "parakram": ["पराक्रम", "वीरता", "साहस"],

    # Darshan & Spiritual Realization
    "darshan": ["दर्शन", "साक्षात्कार", "आत्मदर्शन", "सुलभ दर्शन", "दिव्य दर्शन"],
    "darshana": ["दर्शन", "साक्षात्कार", "आत्मदर्शन"],
    "divine vision": ["दर्शन", "साक्षात्कार", "दिव्य दर्शन"],
    "realization": ["साक्षात्कार", "आत्म-साक्षात्कार", "आत्मदर्शन"],
    "lord gayatri": ["गायत्री", "वेदमाता", "माँ गायत्री", "आद्याशक्ति"],
    "mother gayatri": ["माँ गायत्री", "गायत्री", "वेदमाता"],
    "aadya shakti": ["आद्याशक्ति", "गायत्री शक्ति", "ब्रह्म-तेज"],
    "brahma tej": ["ब्रह्म-तेज", "दिव्य प्रकाश", "ज्योति रूप"],
    "hansvahini": ["हंसवाहिनी", "कमलासन", "साकार रूप"],

    # Gayatri & Mantra
    "gayatri": ["गायत्री", "वेदमाता", "गायत्री महाविज्ञान"],
    "gayatri mantra": ["गायत्री महामन्त्र", "महामन्त्र", "गायत्री मन्त्र"],
    "mantra": ["मन्त्र", "मंत्र"],
    "veda": ["वेद", "ऋक्", "यजुः", "साम", "अथर्व"],
    "vedas": ["वेद", "वेदमाता"],
    "shakti": ["शक्ति", "शक्ति-कोशों"],
    "kamdhenu": ["कामधेनु"],
    "24 akshar": ["२४ अक्षर", "चौबीस अक्षर", "योग-ग्रन्थियाँ"],
    "24 syllables": ["२४ अक्षर", "योग-ग्रन्थियाँ"],
    "yogic granthiyan": ["योग-ग्रन्थियाँ", "सूक्ष्म ग्रन्थियाँ"],
    "glands": ["ग्रन्थियाँ", "योग-ग्रन्थियाँ"],

    # 24 Glands & Syllables
    "tapini": ["तापिनी", "सफलता", "तत्"],
    "saphala": ["सफला", "पराक्रम", "स"],
    "vishwa": ["विश्वा", "पालन", "वि"],
    "tushti": ["तुष्टि", "कल्याण", "तु"],
    "varada": ["वरदा", "योग", "व"],
    "revati": ["रेवती", "प्रेम", "रे"],
    "sookshma": ["सूक्ष्मा", "धन", "णि"],
    "gyana": ["ज्ञाना", "तेज", "यं"],
    "bharga": ["भर्गा", "रक्षा", "भर्"],
    "gomati": ["गोमती", "बुद्धि", "गो"],
    "devika": ["देविका", "दमन", "दे"],
    "varahi": ["वराही", "निष्ठा", "व"],
    "simhani": ["सिंहनी", "धारणा", "स्य"],
    "dhyana": ["ध्याना", "प्राण", "धी"],
    "maryada": ["मर्यादा", "संयम", "म"],
    "sphuta": ["स्फुटा", "तप", "हि"],
    "medha": ["मेधा", "दूरदर्शिता", "धि"],
    "yogamaya": ["योगमाया", "जागृति", "यो"],
    "yogini": ["योगिनी", "उत्पादन", "यो"],
    "dharini": ["धारिणी", "सरसता", "नः"],
    "prabhava": ["प्रभवा", "आदर्श", "प्र"],
    "ooshma": ["ऊष्मा", "साहस", "चो"],
    "drishya": ["दृश्या", "विवेक", "द"],
    "niranjana": ["निरञ्जना", "सेवा", "यात्"],

    # 5 Koshas (Pancha-Koshas)
    "pancha-kosha": ["पञ्चकोश", "अन्नमय", "प्राणमय", "मनोमय", "विज्ञानमय", "आनन्दमय"],
    "panchakosh": ["पञ्चकोश", "पाँच कोश"],
    "five sheaths": ["पञ्चकोश", "५ कोश"],
    "annamaya": ["अन्नमय कोश", "स्थूल शरीर", "उपवास", "आसन"],
    "pranamaya": ["प्राणमय कोश", "प्राणायाम", "प्राणाकर्षण", "बन्ध", "मुद्रा"],
    "manomaya": ["मनोमय कोश", "ध्यान", "त्राटक", "तन्मात्रा"],
    "vigyanamaya": ["विज्ञानमय कोश", "सोऽहम्", "आत्मानुभूति", "स्वर योग"],
    "anandamaya": ["आनन्दमय कोश", "नाद साधना", "तुरीयावस्था", "परमानन्द"],
    "panchamukhi": ["पञ्चमुखी गायत्री", "पञ्चकोश"],

    # 7 Vyahritis
    "vyahriti": ["व्याहृतियाँ", "भूः", "भुवः", "स्वः", "महः", "जनः", "तपः", "सत्यम्"],
    "vyahritis": ["व्याहृतियाँ", "७ व्याहृतियाँ"],
    "bhooh": ["भूः", "पृथ्वी लोक"],
    "bhuvah": ["भुवः", "अंतरिक्ष लोक"],
    "swah": ["स्वः", "स्वर्ग लोक"],

    # Shat-Chakra & Kundalini
    "shat-chakra": ["षट्चक्र", "मूलाधार", "स्वाधिष्ठान", "मणिपूर", "अनाहत", "विशुद्धाख्य", "आज्ञा"],
    "six chakras": ["षट्चक्र", "चक्र"],
    "chakras": ["षट्चक्र", "चक्र"],
    "kundalini": ["कुण्डलिनी", "षट्चक्र वेधन", "कुण्डलिनी पीड़न"],
    "muladhara": ["मूलाधार", "पृथ्वी तत्व", "लं"],
    "swadhisthana": ["स्वाधिष्ठान", "जल तत्व", "बं"],
    "manipura": ["मणिपूर", "नाभि", "अग्नि तत्व", "रं"],
    "anahata": ["अनाहत", "हृदय", "वायु तत्व", "यं"],
    "vishuddha": ["विशुद्धाख्य", "कण्ठ", "आकाश तत्व", "हं"],
    "ajna": ["आज्ञा चक्र", "भ्रूमध्य", "ॐ"],
    "sahasrara": ["सहस्रार", "शून्य चक्र"],
    "nadi": ["नाड़ी", "इड़ा", "पिङ्गला", "सुषुम्णा"],
    "nadis": ["नाड़ियाँ", "इड़ा", "पिङ्गला", "सुषुम्णा"],
    "ida": ["इड़ा", "चन्द्र नाड़ी"],
    "pingala": ["पिङ्गला", "सूर्य नाड़ी"],
    "sushumna": ["सुषुम्णा", "केन्द्रीय नाड़ी"],

    # 10 Tapas
    "tapas": ["१० प्रकार के तप", "तप साधना", "तपस्या"],
    "ten tapas": ["१० प्रकार के तप"],
    "10 tapas": ["१० प्रकार के तप"],
    "asvada": ["अस्वाद तप", "नमक मीठे का त्याग"],
    "titiksha": ["तितिक्षा तप", "सहनशीलता"],
    "karshana": ["कर्षण तप", "सादगी", "शारीरिक सेवा"],
    "upavasa": ["उपवास", "नींबू-पानी"],
    "fasting": ["उपवास", "साधना"],
    "gavya kalpa": ["गव्य कल्प", "पंचगव्य"],
    "pradatavya": ["प्रदातव्य तप", "दान", "लोक-सेवा"],
    "nishkasana": ["निष्कासन तप", "पाप-प्रकाशन"],
    "chandrayana": ["चान्द्रायण व्रत", "चान्द्रायण तप"],

    # Yajna & Yagyopaveet
    "yagya": ["यज्ञ", "यज्ञीय", "हवन"],
    "yajna": ["यज्ञ", "यज्ञीय", "हवन"],
    "havan": ["यज्ञ", "हवन"],
    "yagyopaveet": ["यज्ञोपवीत", "जनेऊ", "द्विजत्व"],
    "janeu": ["जनेऊ", "यज्ञोपवीत", "तीन लड़ियाँ"],
    "sacred thread": ["यज्ञोपवीत", "जनेऊ"],
    "sandhyavandan": ["सन्ध्यावन्दन", "पञ्च-कर्म"],
    "shikha-bandhan": ["शिखा-बन्धन", "विद्युत् केन्द्र"],

    # Women's Vedic Rights
    "women": ["स्त्रियाँ", "नारी", "महिलाएं", "देवियाँ"],
    "women rights": ["स्त्रियों के वेद अधिकार", "नारी", "वेदाध्ययन"],
    "nari": ["नारी", "स्त्रियाँ", "महिलाएं"],
    "stree": ["स्त्रियाँ", "नारी"],
    "gargi": ["गार्गी", "ब्रह्मवादिनी"],
    "maitreyi": ["मैत्रेयी", "ब्रह्मवादिनी"],
    "harita dharmasutra": ["हारीत धर्मसूत्र", "ब्रह्मवादिन्यः"],
    "malaviya": ["मदन मोहन मालवीय", "काशी हिन्दू विश्वविद्यालय"],

    # Specific Applications & Crisis
    "raksha-kavach": ["गायत्री रक्षा-कवच", "भोजपत्र", "ताबीज"],
    "raksha kavach": ["गायत्री रक्षा-कवच", "भोजपत्र", "ताबीज"],
    "protective amulet": ["गायत्री रक्षा-कवच"],
    "anushthan": ["लघु अनुष्ठान", "पूर्ण अनुष्ठान", "२४०००", "सवा लाख"],
    "snake bite": ["सर्प-विष", "हवन भस्म"],
    "daridrata": ["दरिद्रता", "कर्ज", "श्रीं बीज"],
    "poverty": ["दरिद्रता", "कर्ज", "श्रीं बीज"],
    # Shaap Vimochan (Curse Removal myth & reality)
    "sapvimochan": ["शाप विमोचन", "शापोद्धार", "गायत्री शाप", "shaap vimochan", "curse removal"],
    "shapvimochan": ["शाप विमोचन", "शापोद्धार", "गायत्री शाप", "shaap vimochan", "curse removal"],
    "shaap vimochan": ["शाप विमोचन", "शापोद्धार", "गायत्री शाप", "curse removal"],
    "shapa vimochana": ["शाप विमोचन", "शापोद्धार", "गायत्री शाप", "curse removal"],
    "curse removal": ["शाप विमोचन", "शापोद्धार", "shaap vimochan"],

    # Self-Introspection & Sadhana Pillars
    "spect ourselves": ["आत्म-निरीक्षण", "आत्म-सुधार", "आत्म-परीक्षण", "introspect", "self examination"],
    "spect": ["आत्म-निरीक्षण", "आत्म-सुधार", "introspect", "introspection"],
    "introspect": ["आत्म-निरीक्षण", "आत्म-समीक्षा", "आत्म-सुधार", "self-introspection"],
    "introspection": ["आत्म-निरीक्षण", "आत्म-सुधार", "आत्म-विकास", "self-reflection"],
    "self examination": ["आत्म-निरीक्षण", "आत्म-समीक्षा", "introspection"],
    "atma nirikshan": ["आत्म-निरीक्षण", "आत्म-सुधार", "आत्म-विकास", "आत्म-निर्माण", "introspection"],
}


class QueryNormalizer:
    """Preserves user query while expanding Hinglish and conceptual terms for retrieval."""

    @staticmethod
    def normalize_query(query: str) -> Tuple[str, List[str], str]:
        """Normalize query for retrieval.

        Returns: (expanded_query, matched_glossary_terms, detected_lang)
        """
        orig = query.strip()
        lang = detect_language(orig)
        lower = orig.lower()

        matched_terms: List[str] = []
        expanded_keywords: List[str] = []

        for key, terms in TERM_GLOSSARY.items():
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, lower, re.IGNORECASE):
                matched_terms.append(key)
                expanded_keywords.extend(terms)

        # Build retrieval query without altering the user's original query text
        if expanded_keywords:
            unique_kws = list(dict.fromkeys(expanded_keywords))
            expanded_query = f"{orig} {' '.join(unique_kws[:6])}"
        else:
            expanded_query = orig

        return expanded_query, matched_terms, lang

    @classmethod
    def normalize(cls, query: str) -> str:
        """Convenience method returning expanded query string."""
        expanded, _, _ = cls.normalize_query(query)
        return expanded


query_normalizer = QueryNormalizer()
