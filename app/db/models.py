import uuid
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class DocumentModel(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    author: str = "Pandit Shriram Sharma Acharya"
    source_type: Literal["book", "speech", "discourse", "article"] = "book"
    publication: Optional[str] = "युग निर्माण योजना विस्तार ट्रस्ट, गायत्री तपोभूमि, मथुरा"
    edition: Optional[str] = "संयुक्त संस्करण सन् २०१०"
    source_url: Optional[str] = None
    file_path: str
    file_hash: str
    total_pages: int
    language: Literal["hi", "en", "mixed"] = "hi"
    copyright_status: Literal["approved", "pending", "restricted"] = "approved"
    quality_status: Literal["pending", "approved", "rejected"] = "approved"
    created_at: str = Field(default_factory=lambda: "2026-10-04T12:00:00Z")


class DocumentPageModel(BaseModel):
    page_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    pdf_page_index: int  # 0-indexed in PDF
    printed_page_number: int  # Actual printed page in book
    raw_text: str
    cleaned_text: str
    extraction_method: Literal["pdf_text", "ocr"] = "ocr"
    ocr_confidence: Optional[float] = 1.0
    quality_status: Literal["pending", "approved", "rejected"] = "approved"
    has_issues: bool = False
    issue_reason: Optional[str] = None


class DocumentChunkModel(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    document_version: str = "1.0"
    content: str
    book: str
    author: str = "Pandit Shriram Sharma Acharya"
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_start: int
    page_end: int
    language: Literal["hi", "en", "mixed"] = "hi"
    source_type: Literal["book", "speech", "discourse", "article"] = "book"
    edition: Optional[str] = "संयुक्त संस्करण सन् २०१०"
    publication: Optional[str] = "युग निर्माण योजना विस्तार ट्रस्ट, गायत्री तपोभूमि, मथुरा"
    source_url: Optional[str] = None
    copyright_status: Literal["approved", "pending", "restricted"] = "approved"
    quality_status: Literal["pending", "approved", "rejected"] = "approved"
    extraction_method: Literal["pdf_text", "ocr"] = "ocr"
    ocr_confidence: Optional[float] = 1.0
    content_hash: str
    parser_version: str = "1.0"
    chunker_version: str = "1.0"
    embedding_model: str = "all-MiniLM-L6-v2"

    def to_metadata(self) -> Dict[str, Any]:
        """Convert chunk metadata to flat dictionary for ChromaDB and vector stores."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_version": self.document_version,
            "book": self.book or "",
            "author": self.author or "",
            "chapter": self.chapter or "",
            "section": self.section or "",
            "page_start": int(self.page_start),
            "page_end": int(self.page_end),
            "language": self.language,
            "source_type": self.source_type,
            "edition": self.edition or "",
            "publication": self.publication or "",
            "source_url": self.source_url or "",
            "copyright_status": self.copyright_status,
            "quality_status": self.quality_status,
            "extraction_method": self.extraction_method,
            "ocr_confidence": float(self.ocr_confidence or 1.0),
            "content_hash": self.content_hash,
            "parser_version": self.parser_version,
            "chunker_version": self.chunker_version,
            "embedding_model": self.embedding_model,
        }


class SourceCitation(BaseModel):
    chunk_id: str
    document_id: str
    book: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_start: int
    page_end: int
    source_type: str = "book"


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "hi"


class ChatResponse(BaseModel):
    answer: str
    evidence_status: Literal["supported", "partial_support", "insufficient_evidence"]
    retrieval_confidence: Literal["high", "medium", "low", "insufficient_evidence"]
    sources: List[SourceCitation]
    conversation_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_quality: bool = True


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total_found: int
    confidence: Literal["high", "medium", "low", "insufficient_evidence"]
