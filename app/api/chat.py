from fastapi import APIRouter
from app.config import settings
from app.db.models import ChatRequest, ChatResponse
from app.retrieval.hybrid_search import hybrid_search_engine
from app.generation.answer_generator import answer_generator

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Source-grounded chat endpoint with strict citation validation and safe abstention."""
    # 1. Retrieve candidates
    results, confidence = hybrid_search_engine.search(
        query=req.question,
        top_k=settings.RETRIEVAL_TOP_K,
        use_hybrid=True,
    )

    # 2. Evidence-first generation
    response = answer_generator.generate_answer(
        question=req.question,
        retrieved_items=results,
        retrieval_confidence=confidence,
        language=req.language,
        conversation_id=req.conversation_id,
    )

    return response
