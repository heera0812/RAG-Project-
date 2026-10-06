import re
import unicodedata


def clean_hindi_text(text: str) -> str:
    """Clean and normalize Hindi / Sanskrit Devanagari text."""
    if not text:
        return ""

    # 1. Unicode NFC normalization (combines base characters and matras correctly)
    normalized = unicodedata.normalize("NFC", text)

    # 2. Fix OCR artifacts and common character confusions
    # Normalize danda and double danda
    normalized = normalized.replace("|", "।")
    normalized = re.sub(r"।\s*।", "॥", normalized)

    # 3. Fix hyphenated line wraps (e.g., "आत्म-\nसंयम" -> "आत्म-संयम")
    normalized = re.sub(r"([^\s])-[\r\n]+([^\s])", r"\1-\2", normalized)

    # 4. Remove isolated header/footer artifacts
    lines = normalized.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip isolated running book title header if already known
        if stripped in ["गायत्री महाविज्ञान", "गायत्री महाविज्ञान प्रथम भाग"]:
            continue
        # Skip isolated page numbers (Devanagari or Western digits) alone on a line
        if re.match(r"^[\d०-९\s\-\.\*]+$", stripped) and len(stripped) < 10:
            continue
        cleaned_lines.append(stripped)

    # Reassemble paragraphs
    cleaned_text = "\n".join(cleaned_lines)
    # Collapse 3 or more consecutive newlines to 2
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    # Collapse multiple spaces
    cleaned_text = re.sub(r"[ \t]{2,}", " ", cleaned_text)

    return cleaned_text.strip()
