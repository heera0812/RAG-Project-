import os
import json
import sqlite3
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
import chromadb.utils.embedding_functions as ef

from app.config import settings
from app.db.models import (
    DocumentModel,
    DocumentPageModel,
    DocumentChunkModel,
    SearchResultItem,
)


class MetadataRepository:
    """Persistent SQLite-backed repository for Document, Page, and Chunk provenance."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or settings.DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT,
                    source_type TEXT,
                    publication TEXT,
                    edition TEXT,
                    source_url TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    total_pages INTEGER,
                    language TEXT,
                    copyright_status TEXT,
                    quality_status TEXT,
                    created_at TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_pages (
                    page_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    pdf_page_index INTEGER,
                    printed_page_number INTEGER,
                    raw_text TEXT,
                    cleaned_text TEXT,
                    extraction_method TEXT,
                    ocr_confidence REAL,
                    quality_status TEXT,
                    has_issues INTEGER,
                    issue_reason TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    document_version TEXT,
                    content TEXT,
                    book TEXT,
                    author TEXT,
                    chapter TEXT,
                    section TEXT,
                    page_start INTEGER,
                    page_end INTEGER,
                    language TEXT,
                    source_type TEXT,
                    edition TEXT,
                    publication TEXT,
                    source_url TEXT,
                    copyright_status TEXT,
                    quality_status TEXT,
                    extraction_method TEXT,
                    ocr_confidence REAL,
                    content_hash TEXT,
                    parser_version TEXT,
                    chunker_version TEXT,
                    embedding_model TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TEXT
                )
            """
            )
            conn.commit()

    def save_document(self, doc: DocumentModel):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    doc.document_id,
                    doc.title,
                    doc.author,
                    doc.source_type,
                    doc.publication,
                    doc.edition,
                    doc.source_url,
                    doc.file_path,
                    doc.file_hash,
                    doc.total_pages,
                    doc.language,
                    doc.copyright_status,
                    doc.quality_status,
                    doc.created_at,
                ),
            )
            conn.commit()

    def get_document(self, document_id: str) -> Optional[DocumentModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            if row:
                return DocumentModel(**dict(row))
        return None

    def list_documents(self) -> List[DocumentModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            return [DocumentModel(**dict(r)) for r in cursor.fetchall()]

    def save_page(self, page: DocumentPageModel):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO document_pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    page.page_id,
                    page.document_id,
                    page.pdf_page_index,
                    page.printed_page_number,
                    page.raw_text,
                    page.cleaned_text,
                    page.extraction_method,
                    page.ocr_confidence,
                    page.quality_status,
                    1 if page.has_issues else 0,
                    page.issue_reason,
                ),
            )
            conn.commit()

    def get_page(self, document_id: str, printed_page_number: int) -> Optional[DocumentPageModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM document_pages WHERE document_id = ? AND printed_page_number = ?",
                (document_id, printed_page_number),
            )
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["has_issues"] = bool(d["has_issues"])
                return DocumentPageModel(**d)
        return None

    def list_pages_for_document(self, document_id: str) -> List[DocumentPageModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM document_pages WHERE document_id = ? ORDER BY printed_page_number ASC",
                (document_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["has_issues"] = bool(d["has_issues"])
                results.append(DocumentPageModel(**d))
            return results

    def save_chunk(self, chunk: DocumentChunkModel):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO document_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.document_version,
                    chunk.content,
                    chunk.book,
                    chunk.author,
                    chunk.chapter,
                    chunk.section,
                    chunk.page_start,
                    chunk.page_end,
                    chunk.language,
                    chunk.source_type,
                    chunk.edition,
                    chunk.publication,
                    chunk.source_url,
                    chunk.copyright_status,
                    chunk.quality_status,
                    chunk.extraction_method,
                    chunk.ocr_confidence,
                    chunk.content_hash,
                    chunk.parser_version,
                    chunk.chunker_version,
                    chunk.embedding_model,
                ),
            )
            conn.commit()

    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunkModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            if row:
                return DocumentChunkModel(**dict(row))
        return None

    def list_chunks_for_document(self, document_id: str) -> List[DocumentChunkModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM document_chunks WHERE document_id = ? ORDER BY page_start ASC",
                (document_id,),
            )
            return [DocumentChunkModel(**dict(r)) for r in cursor.fetchall()]

    def count_chunks(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            return cursor.fetchone()[0]


class VectorRepository:
    """ChromaDB vector store repository managing approved chunk embeddings and similarity search."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = str(persist_dir or settings.CHROMA_PERSIST_DIR)
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_fn = ef.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[DocumentChunkModel]):
        if not chunks:
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = [c.to_metadata() for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    def _init_chroma(self):
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_approved_only: bool = True,
    ) -> List[SearchResultItem]:
        where_filter = None
        if filter_approved_only:
            where_filter = {
                "$and": [
                    {"quality_status": {"$eq": "approved"}},
                    {"copyright_status": {"$eq": "approved"}},
                ]
            }

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            try:
                self._init_chroma()
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception:
                return []

        items: List[SearchResultItem] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return items

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else [""] * len(ids)
        metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(ids)
        distances = results["distances"][0] if results["distances"] else [1.0] * len(ids)

        for chunk_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
            # Chroma with cosine distance: distance = 1 - cosine_similarity
            similarity_score = max(0.0, min(1.0, 1.0 - float(dist)))
            doc_id = meta.get("document_id", "")
            items.append(
                SearchResultItem(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    content=doc_text,
                    score=round(similarity_score, 4),
                    metadata=meta,
                )
            )

        return items

    def count(self) -> int:
        return self.collection.count()


metadata_repo = MetadataRepository()
vector_repo = VectorRepository()
