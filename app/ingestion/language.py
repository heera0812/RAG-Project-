import re
from typing import Literal


def detect_language(text: str) -> Literal["hi", "en", "mixed"]:
    """Detect if text is primarily Hindi (Devanagari), English (Latin), or Mixed/Hinglish."""
    if not text:
        return "hi"

    # Count Devanagari characters: Unicode block \u0900-\u097F
    devanagari_count = len(re.findall(r"[\u0900-\u097F]", text))
    # Count Latin alphabetic characters
    latin_count = len(re.findall(r"[a-zA-Z]", text))

    total = devanagari_count + latin_count
    if total == 0:
        return "hi"

    # If both scripts are present with meaningful presence, it's mixed
    if devanagari_count >= 5 and latin_count >= 5:
        return "mixed"

    # Check for common Hinglish Romanized Hindi words (e.g. kya, kaise, karein, kyu, hai, hain)
    hinglish_markers = [
        "kya", "kaise", "kyu", "kyon", "karein", "karna", "hoga", "sakte", "sakti",
        "hain", "nahi", "hota", "gussa", "sadhana", "samay", "jeevan", "mein"
    ]
    lower = text.lower()
    matches = sum(1 for m in hinglish_markers if re.search(r"\b" + m + r"\b", lower))
    if matches >= 2:
        return "mixed"

    dev_ratio = devanagari_count / total
    if dev_ratio >= 0.70:
        return "hi"
    elif dev_ratio <= 0.30:
        return "en"
    else:
        return "mixed"


def is_devanagari_script(text: str) -> bool:
    """Return True if text contains significant Devanagari characters."""
    return len(re.findall(r"[\u0900-\u097F]", text)) > 5
