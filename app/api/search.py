from fastapi import APIRouter
from app.db.models import SearchRequest, SearchResponse
from app.retrieval.hybrid_search import hybrid_search_engine

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_chunks(req: SearchRequest):
    """Search authorized knowledge chunks by query."""
    results, confidence = hybrid_search_engine.search(
        query=req.query,
        top_k=req.top_k,
        use_hybrid=True,
    )
    return SearchResponse(
        query=req.query,
        results=results,
        total_found=len(results),
        confidence=confidence,
    )
