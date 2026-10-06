from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.config import settings
from app.db.models import DocumentModel
from app.ingestion.pdf_parser import pdf_pipeline
from app.db.repositories import metadata_repo

router = APIRouter(prefix="/api", tags=["ingest"])


class IngestRequest(BaseModel):
    file_path: Optional[str] = None
    title: Optional[str] = "गायत्री महाविज्ञान [ संयुक्त संस्करण ]"
    author: Optional[str] = "Pandit Shriram Sharma Acharya"
    page_offset: int = 10
    start_page: int = 1
    end_page: Optional[int] = 30


@router.post("/ingest", response_model=DocumentModel)
def ingest_document(req: IngestRequest):
    """Ingest an authorized source document into the knowledge base."""
    target_path = req.file_path or str(settings.RAW_DATA_DIR / "Mahavigyan.pdf")
    try:
        doc = pdf_pipeline.ingest_pdf(
            pdf_path=target_path,
            title=req.title or "गायत्री महाविज्ञान [ संयुक्त संस्करण ]",
            author=req.author or "Pandit Shriram Sharma Acharya",
            page_offset=req.page_offset,
            start_page=req.start_page,
            end_page=req.end_page,
        )
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
