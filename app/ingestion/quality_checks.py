import re
from typing import Tuple, Optional
from app.config import settings
from app.db.models import DocumentChunkModel


class QualityChecker:
    """Validates pages and chunks against quality gates per Section 5."""

    @staticmethod
    def check_page_text(text: str) -> Tuple[bool, Optional[str]]:
        """Check if page text meets quality threshold."""
        if not text or len(text.strip()) == 0:
            return False, "Empty page text"

        stripped = text.strip()
        if len(stripped) < 40:
            return False, f"Page text too short ({len(stripped)} chars)"

        # Check for Unicode replacement character \ufffd (broken Unicode)
        if "\ufffd" in stripped:
            return False, "Contains replacement character (broken Unicode)"

        symbol_count = len(re.findall(r"[\^~`_§±×÷¶†‡]", stripped))
        if symbol_count > 10:
            return False, f"Excessive OCR garbage symbols detected ({symbol_count})"

        # Check for Devanagari character presence
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", stripped))
        if devanagari_chars < 15:
            return False, "Insufficient Devanagari text on page"

        return True, None

    @staticmethod
    def check_chunk(chunk: DocumentChunkModel) -> Tuple[bool, Optional[str]]:
        """Check if a chunk meets quality gates for indexing."""
        if not chunk.content or len(chunk.content.strip()) == 0:
            return False, "Empty chunk content"

        content_len = len(chunk.content.strip())
        if content_len < settings.MIN_CHUNK_CHARS:
            return False, f"Chunk too short ({content_len} chars, minimum {settings.MIN_CHUNK_CHARS})"

        if not chunk.document_id:
            return False, "Missing document_id"

        if chunk.page_start <= 0 or chunk.page_end <= 0:
            return False, "Invalid page range (must be positive)"

        if chunk.page_start > chunk.page_end:
            return False, f"Invalid page range: start ({chunk.page_start}) > end ({chunk.page_end})"

        if not chunk.book:
            return False, "Missing book title in metadata"

        if chunk.copyright_status != "approved":
            return False, f"Unapproved copyright status: {chunk.copyright_status}"

        # Broken Unicode check
        if "\ufffd" in chunk.content:
            return False, "Contains broken Unicode character"

        return True, None
