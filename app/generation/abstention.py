from app.config import settings
from app.db.models import ChatResponse


def get_abstention_text(language: str = "hi") -> str:
    """Return non-negotiable standardized abstention response per Section 2."""
    if language == "en":
        return settings.ABSTENTION_EN
    return settings.ABSTENTION_HI


def build_abstention_response(language: str = "hi", conversation_id: str = None) -> ChatResponse:
    """Build a formal abstention ChatResponse object."""
    return ChatResponse(
        answer=get_abstention_text(language),
        evidence_status="insufficient_evidence",
        retrieval_confidence="insufficient_evidence",
        sources=[],
        conversation_id=conversation_id,
    )
