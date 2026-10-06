from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router

__all__ = [
    "health_router",
    "documents_router",
    "search_router",
    "chat_router",
    "ingest_router",
]
