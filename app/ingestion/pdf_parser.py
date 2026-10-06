import os
import hashlib
from pathlib import Path
from typing import List, Optional, Callable
import pymupdf

from app.config import settings
from app.db.models import DocumentModel, DocumentPageModel, DocumentChunkModel
from app.db.repositories import metadata_repo, vector_repo
from app.ingestion.cleaner import clean_hindi_text
from app.ingestion.language import detect_language
from app.ingestion.quality_checks import QualityChecker
from app.ingestion.ocr import ocr_engine
from app.ingestion.chunker import chunker


class PDFIngestionPipeline:
    """End-to-end PDF ingestion pipeline adhering to Section 5."""

    def __init__(self):
        self.ocr = ocr_engine
        self.chunker = chunker

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def ingest_pdf(
        self,
        pdf_path: str,
        title: str = "गायत्री महाविज्ञान [ संयुक्त संस्करण ]",
        author: str = "Pandit Shriram Sharma Acharya",
        page_offset: int = 10,  # PDF page index 10 = printed page 1
        start_page: int = 1,     # 1-indexed printed page
        end_page: Optional[int] = 30, # printed page limit for milestone
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> DocumentModel:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found at {pdf_path}")

        file_hash = self.compute_file_hash(str(pdf_file))
        doc = pymupdf.open(str(pdf_file))
        total_pdf_pages = len(doc)

        # 1. Create Document Record
        existing_docs = [d for d in metadata_repo.list_documents() if d.file_hash == file_hash]
        if existing_docs:
            document_record = existing_docs[0]
        else:
            document_record = DocumentModel(
                title=title,
                author=author,
                source_type="book",
                file_path=str(pdf_file),
                file_hash=file_hash,
                total_pages=total_pdf_pages,
                language="hi",
                copyright_status="approved",
                quality_status="approved",
            )
            metadata_repo.save_document(document_record)

        doc_slug = "gayatri_mahavigyan"
        max_printed = end_page if end_page else (total_pdf_pages - page_offset)

        # 2. Extract and Process Pages
        extracted_pages: List[DocumentPageModel] = []
        for printed_p in range(start_page, max_printed + 1):
            pdf_idx = printed_p + page_offset - 1
            if pdf_idx >= total_pdf_pages:
                break

            if progress_callback:
                progress_callback(printed_p, max_printed, f"Processing page {printed_p}")

            # Check if digital text exists
            page_obj = doc[pdf_idx]
            extracted_text = page_obj.get_text().strip()

            if len(extracted_text) > 80:
                raw_text = extracted_text
                confidence = 1.0
                has_issues = False
                issue_reason = None
                method = "pdf_text"
            else:
                # Render to image and OCR
                pix = page_obj.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                raw_text, confidence, has_issues, issue_reason = self.ocr.extract_page_ocr(
                    image_bytes=img_bytes,
                    doc_slug=doc_slug,
                    page_number=printed_p,
                )
                method = "ocr"

            cleaned_text = clean_hindi_text(raw_text)
            page_quality = "rejected" if has_issues else "approved"

            page_record = DocumentPageModel(
                document_id=document_record.document_id,
                pdf_page_index=pdf_idx,
                printed_page_number=printed_p,
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                extraction_method=method,
                ocr_confidence=confidence,
                quality_status=page_quality,
                has_issues=has_issues,
                issue_reason=issue_reason,
            )
            metadata_repo.save_page(page_record)
            if not has_issues and len(cleaned_text) > 40:
                extracted_pages.append(page_record)

        # 3. Create Structure-Aware Chunks
        raw_chunks = self.chunker.chunk_pages(
            pages=extracted_pages,
            document_id=document_record.document_id,
            book_title=title,
            author=author,
        )

        # 4. Run Quality Checks and Filter Approved Chunks
        approved_chunks: List[DocumentChunkModel] = []
        for chk in raw_chunks:
            is_valid, reason = QualityChecker.check_chunk(chk)
            if is_valid:
                chk.quality_status = "approved"
                approved_chunks.append(chk)
            else:
                chk.quality_status = "rejected"

            metadata_repo.save_chunk(chk)

        # 5. Embed and Index in ChromaDB
        if approved_chunks:
            vector_repo.add_chunks(approved_chunks)

        return document_record


pdf_pipeline = PDFIngestionPipeline()
