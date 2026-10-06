import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional

from app.config import settings
from app.db.models import DocumentPageModel, DocumentChunkModel


class StructureAwareChunker:
    """Structure-aware chunker adhering to Rule 6:

    Book -> Chapter -> Section -> Paragraph group -> Chunk
    """

    def __init__(
        self,
        target_chars: int = settings.CHUNK_TARGET_CHARS,
        overlap_chars: int = settings.CHUNK_OVERLAP_CHARS,
    ):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    @staticmethod
    def _is_heading(line: str) -> bool:
        """Heuristic to detect Hindi chapter or section titles."""
        line = line.strip()
        if not line or len(line) > 80:
            return False
        # Matches patterns like "१. वेदमाता गायत्री की उत्पत्ति", "गायत्री ही कामधेनु है", "भूमिका"
        if re.match(r"^[०-९\d]+[\.\-\s]+[^\।\॥\?\!]+$", line):
            return True
        if line.startswith("अध्याय") or line.startswith("प्रकरण") or line.startswith("खण्ड"):
            return True
        # Short lines without sentence terminators
        if not any(line.endswith(p) for p in ["।", "॥", "!", "?", ".", ":"]) and len(line) < 50:
            return True
        return False

    def chunk_pages(
        self,
        pages: List[DocumentPageModel],
        document_id: str,
        book_title: str,
        author: str = "Pandit Shriram Sharma Acharya",
    ) -> List[DocumentChunkModel]:
        """Convert consecutive document pages into structure-aware chunks."""
        chunks: List[DocumentChunkModel] = []
        if not pages:
            return chunks

        current_chapter: Optional[str] = None
        current_section: Optional[str] = None
        current_paragraphs: List[str] = []
        chunk_page_start = pages[0].printed_page_number
        current_page_num = pages[0].printed_page_number

        for page in pages:
            current_page_num = page.printed_page_number
            text = page.cleaned_text.strip()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                if self._is_heading(stripped):
                    # Flush accumulated paragraphs if non-empty
                    if current_paragraphs:
                        section_chunks = self._build_chunks(
                            paragraphs=current_paragraphs,
                            document_id=document_id,
                            book_title=book_title,
                            author=author,
                            chapter=current_chapter,
                            section=current_section,
                            page_start=chunk_page_start,
                            page_end=current_page_num,
                        )
                        chunks.extend(section_chunks)
                        current_paragraphs = []
                        chunk_page_start = current_page_num

                    # Set new heading
                    if "अध्याय" in stripped or (stripped.startswith("१.") or stripped.startswith("२.")):
                        current_chapter = stripped
                        current_section = None
                    else:
                        current_section = stripped
                else:
                    current_paragraphs.append(stripped)

        # Flush any remaining paragraphs
        if current_paragraphs:
            section_chunks = self._build_chunks(
                paragraphs=current_paragraphs,
                document_id=document_id,
                book_title=book_title,
                author=author,
                chapter=current_chapter,
                section=current_section,
                page_start=chunk_page_start,
                page_end=current_page_num,
            )
            chunks.extend(section_chunks)

        return chunks

    def _build_chunks(
        self,
        paragraphs: List[str],
        document_id: str,
        book_title: str,
        author: str,
        chapter: Optional[str],
        section: Optional[str],
        page_start: int,
        page_end: int,
    ) -> List[DocumentChunkModel]:
        chunks: List[DocumentChunkModel] = []
        if not paragraphs:
            return chunks

        combined_text = "\n\n".join(paragraphs).strip()
        if not combined_text:
            return chunks

        # If fits within target size, create one chunk
        if len(combined_text) <= self.target_chars:
            header_prefix = ""
            if chapter:
                header_prefix += f"[{chapter}]\n"
            if section and section != chapter:
                header_prefix += f"[{section}]\n"
            final_content = (header_prefix + combined_text).strip()

            c_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()
            stable_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{c_hash}"))

            chunks.append(
                DocumentChunkModel(
                    chunk_id=stable_id,
                    document_id=document_id,
                    document_version="1.0",
                    content=final_content,
                    book=book_title,
                    author=author,
                    chapter=chapter,
                    section=section,
                    page_start=page_start,
                    page_end=page_end,
                    language="hi",
                    source_type="book",
                    copyright_status="approved",
                    quality_status="approved",
                    extraction_method="ocr",
                    ocr_confidence=0.95,
                    content_hash=c_hash,
                    parser_version="1.0",
                    chunker_version="1.0",
                    embedding_model=settings.EMBEDDING_MODEL,
                )
            )
            return chunks

        # Fallback recursive-like paragraph splitting
        current_chunk_paras: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > self.target_chars and current_chunk_paras:
                # Emit chunk
                body = "\n\n".join(current_chunk_paras).strip()
                header_prefix = ""
                if chapter:
                    header_prefix += f"[{chapter}]\n"
                if section and section != chapter:
                    header_prefix += f"[{section}]\n"
                final_content = (header_prefix + body).strip()

                c_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()
                stable_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{c_hash}"))

                chunks.append(
                    DocumentChunkModel(
                        chunk_id=stable_id,
                        document_id=document_id,
                        document_version="1.0",
                        content=final_content,
                        book=book_title,
                        author=author,
                        chapter=chapter,
                        section=section,
                        page_start=page_start,
                        page_end=page_end,
                        language="hi",
                        source_type="book",
                        copyright_status="approved",
                        quality_status="approved",
                        extraction_method="ocr",
                        ocr_confidence=0.95,
                        content_hash=c_hash,
                        parser_version="1.0",
                        chunker_version="1.0",
                        embedding_model=settings.EMBEDDING_MODEL,
                    )
                )

                # Keep overlap if possible
                overlap_paras = []
                overlap_len = 0
                for op in reversed(current_chunk_paras):
                    if overlap_len + len(op) <= self.overlap_chars:
                        overlap_paras.insert(0, op)
                        overlap_len += len(op)
                    else:
                        break
                current_chunk_paras = overlap_paras + [p]
                current_len = sum(len(x) for x in current_chunk_paras)
            else:
                current_chunk_paras.append(p)
                current_len += p_len

        if current_chunk_paras:
            body = "\n\n".join(current_chunk_paras).strip()
            header_prefix = ""
            if chapter:
                header_prefix += f"[{chapter}]\n"
            if section and section != chapter:
                header_prefix += f"[{section}]\n"
            final_content = (header_prefix + body).strip()

            c_hash = hashlib.sha256(final_content.encode("utf-8")).hexdigest()
            stable_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{c_hash}"))

            chunks.append(
                DocumentChunkModel(
                    chunk_id=stable_id,
                    document_id=document_id,
                    document_version="1.0",
                    content=final_content,
                    book=book_title,
                    author=author,
                    chapter=chapter,
                    section=section,
                    page_start=page_start,
                    page_end=page_end,
                    language="hi",
                    source_type="book",
                    copyright_status="approved",
                    quality_status="approved",
                    extraction_method="ocr",
                    ocr_confidence=0.95,
                    content_hash=c_hash,
                    parser_version="1.0",
                    chunker_version="1.0",
                    embedding_model=settings.EMBEDDING_MODEL,
                )
            )

        return chunks


chunker = StructureAwareChunker()
