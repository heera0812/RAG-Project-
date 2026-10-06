import json
import logging
from typing import List, Optional
from openai import OpenAI

from app.config import settings
from app.db.models import ChatResponse, SearchResultItem, SourceCitation
from app.generation.prompts import STRICT_SYSTEM_PROMPT, build_context_block
from app.generation.citation_validator import citation_validator
from app.generation.abstention import get_abstention_text, build_abstention_response
from app.ingestion.language import detect_language

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Strictly grounded answer generator with mandatory citation validation."""

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY or "dummy_key",
        )
        self.model = settings.LLM_MODEL

    def generate_answer(
        self,
        question: str,
        retrieved_items: List[SearchResultItem],
        retrieval_confidence: str,
        language: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ChatResponse:
        detected_lang = language or detect_language(question)

        # 1. Non-negotiable abstention if insufficient retrieval evidence
        if retrieval_confidence == "insufficient_evidence" or not retrieved_items:
            logger.info("Abstaining due to insufficient retrieval evidence.")
            return build_abstention_response(
                language=detected_lang,
                conversation_id=conversation_id,
            )

        # 2. Build context
        context_str = build_context_block(retrieved_items)
        user_message = (
            f"Question: {question}\n\n"
            f"Verified Knowledge Base Context:\n{context_str}\n\n"
            f"Provide your answer adhering strictly to the system instructions. "
            f"Ensure response is in {detected_lang}."
        )

        data = None
        candidate_models = [self.model] + [m for m in getattr(settings, "FALLBACK_MODELS", []) if m != self.model]

        for model_name in candidate_models:
            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": STRICT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    timeout=20.0,
                )
                raw_content = (response.choices[0].message.content or "{}").strip()
                clean_json = raw_content
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                data = json.loads(clean_json)
                break
            except Exception as e:
                logger.warning(f"LLM model {model_name} failed: {e}. Trying fallback if available...")

        if not data:
            logger.error("All LLM candidate models failed. Returning canonical abstention.")
            return build_abstention_response(
                language=detected_lang,
                conversation_id=conversation_id,
            )

        evidence_status = data.get("evidence_status", "insufficient_evidence")
        claimed_ids = data.get("used_source_ids", [])
        raw_answer = data.get("answer", "")

        # 3. Mandatory Backend Citation Validation
        validated_sources, is_valid = citation_validator.validate_citations(
            claimed_source_ids=claimed_ids,
            retrieved_items=retrieved_items,
        )

        # If model returned insufficient_evidence or claimed support with zero valid citations
        if evidence_status == "insufficient_evidence":
            return ChatResponse(
                answer=get_abstention_text(detected_lang),
                evidence_status="insufficient_evidence",
                retrieval_confidence=retrieval_confidence,
                sources=[],
                conversation_id=conversation_id,
            )

        if not validated_sources and evidence_status in ["supported", "partial_support"]:
            # Auto-link to top retrieved chunk if context was strong but model omitted IDs
            if retrieved_items and retrieval_confidence in ["high", "medium"]:
                top = retrieved_items[0]
                meta = top.metadata
                validated_sources = [
                    SourceCitation(
                        chunk_id=top.chunk_id,
                        document_id=top.document_id,
                        book=meta.get("book", "गायत्री महाविज्ञान"),
                        chapter=meta.get("chapter"),
                        section=meta.get("section"),
                        page_start=int(meta.get("page_start", 1)),
                        page_end=int(meta.get("page_end", 1)),
                        source_type=meta.get("source_type", "book"),
                    )
                ]
            else:
                return build_abstention_response(
                    language=detected_lang,
                    conversation_id=conversation_id,
                )

        # 4. Output Validation: Enforce AI Role (AI is NOT Guru, AI is NOT Teacher)
        # AI is only: Interpreter + Applicator of Gurudev's thoughts.
        prohibited_phrases = [
            "i am your guru", "as your guru", "as your spiritual teacher",
            "i teach you", "my disciples", "follow my teachings",
            "मैं आपका गुरु", "मैं तुम्हारा गुरु", "मेरे शिष्य", "मैं तुम्हें सिखाता हूँ"
        ]
        for phrase in prohibited_phrases:
            if phrase in raw_answer.lower():
                logger.warning(f"Output validation detected prohibited teacher/guru claim: '{phrase}'. Sanitizing.")
                raw_answer = raw_answer.replace(phrase, "परमपूज्य गुरुदेव के विचारों के अनुसार")

        # Format with structured reflection (Gurudev -> Arth -> Abhyas) if fields provided
        gurudev_msg = data.get("gurudev_sandesh")
        arth_msg = data.get("arth")
        abhyas_msg = data.get("aaj_ka_abhyas")

        formatted_answer = raw_answer
        if gurudev_msg and arth_msg and abhyas_msg:
            # If the model provided the components separately and they aren't already formatted in raw_answer
            if "📖 Gurudev" not in raw_answer and "📖 गुरुदेव" not in raw_answer:
                formatted_answer = (
                    f"📖 Gurudev:\n{gurudev_msg}\n\n"
                    f"🧠 Arth:\n{arth_msg}\n\n"
                    f"🌱 Aaj ka Abhyas:\n{abhyas_msg}"
                )

        return ChatResponse(
            answer=formatted_answer,
            evidence_status=evidence_status,
            retrieval_confidence=retrieval_confidence,
            sources=validated_sources,
            conversation_id=conversation_id,
        )


answer_generator = AnswerGenerator()
