from app.ingestion.cleaner import clean_hindi_text


def test_clean_hindi_text_danda():
    raw = "यह एक वाक्य है | दूसरा वाक्य ||"
    cleaned = clean_hindi_text(raw)
    assert "।" in cleaned
    assert "॥" in cleaned
    assert "|" not in cleaned


def test_clean_hindi_text_hyphen_wrap():
    raw = "गायत्री उपासना से आत्म-\nशान्ति मिलती है।"
    cleaned = clean_hindi_text(raw)
    assert "आत्म-शान्ति" in cleaned


def test_clean_hindi_text_header_stripping():
    raw = "गायत्री महाविज्ञान\n\nवेद कहते हैं ज्ञान को।\n\n१"
    cleaned = clean_hindi_text(raw)
    assert "वेद कहते हैं ज्ञान को।" in cleaned
    assert "गायत्री महाविज्ञान\n" not in cleaned
