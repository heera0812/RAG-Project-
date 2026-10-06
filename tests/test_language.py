from app.ingestion.language import detect_language, is_devanagari_script


def test_detect_language_hindi():
    text = "गायत्री महाविज्ञान वेदमूर्ति तपोनिष्ठ पं० श्रीराम शर्मा आचार्य"
    assert detect_language(text) == "hi"
    assert is_devanagari_script(text) is True


def test_detect_language_english():
    text = "What does Gurudev say about Gayatri sadhana and daily discipline?"
    assert detect_language(text) == "en"
    assert is_devanagari_script(text) is False


def test_detect_language_mixed():
    text = "kya women गायत्री साधना daily life me kar sakti hain?"
    assert detect_language(text) in ["hi", "mixed"]
