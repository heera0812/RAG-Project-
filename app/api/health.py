from fastapi import APIRouter
from app.config import settings
from app.db.repositories import metadata_repo, vector_repo

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health():
    """Health check endpoint providing system status and indexing stats."""
    doc_count = len(metadata_repo.list_documents())
    chunk_count = metadata_repo.count_chunks()
    vector_count = vector_repo.count()

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "documents_indexed": doc_count,
        "chunks_indexed": chunk_count,
        "vector_records": vector_count,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL,
    }
