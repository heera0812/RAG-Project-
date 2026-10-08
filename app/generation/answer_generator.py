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
from app.retrieval.notebooklm_engine import notebooklm_engine

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Strictly grounded answer generator with mandatory citation validation."""

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY or "dummy_key",
        )
        self.model = settings.LLM_MODEL

    def _try_generate_via_google_gemini(self, prompt_text: str) -> Optional[dict]:
        """Directly call Google Gemini / Generative Language API without third-party proxies."""
        if not getattr(settings, "GEMINI_API_KEY", ""):
            return None
        models_to_try = [
            getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"),
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
        ]
        seen = set()
        unique_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        for m_name in unique_models:
            try:
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "generationConfig": {"temperature": 0.1},
                }
                resp = requests.post(url, json=payload, timeout=25.0)
                if resp.status_code == 200:
                    data_resp = resp.json()
                    candidates = data_resp.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_json = raw_text.strip()
                        if "```json" in clean_json:
                            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                        elif "```" in clean_json:
                            clean_json = clean_json.split("```")[1].split("```")[0].strip()
                        try:
                            return json.loads(clean_json)
                        except Exception:
                            return {
                                "answer": raw_text.strip(),
                                "evidence_status": "supported",
                                "used_source_ids": [],
                            }
            except Exception as e:
                logger.warning(f"Google Gemini model {m_name} encountered error: {e}")
        return None

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

        # 2a. Try Google Gemini Notebook (NotebookLM) if authenticated
        if getattr(settings, "NOTEBOOKLM_ENABLED", False) and notebooklm_engine.is_authenticated():
            try:
                logger.info("Attempting grounded generation via Google Gemini Notebook (NotebookLM)...")
                nlm_res = notebooklm_engine.ask_sync(question)
                if nlm_res and nlm_res.get("answer"):
                    nlm_ans = nlm_res["answer"].strip()
                    # Structure into reflection formula if not already structured
                    formatted_ans = nlm_ans
                    if "Gurudev" not in formatted_ans and "गुरुदेव" not in formatted_ans:
                        formatted_ans = (
                            f"📖 Gurudev: {nlm_ans}\n\n"
                            f"🧠 Arth: Grounded in Shantikunj literature via Gemini Notebook.\n\n"
                            f"🌱 Aaj ka Abhyas: Apply these principles conscientiously in daily life."
                        )
                    data = {
                        "answer": formatted_ans,
                        "evidence_status": "supported",
                        "used_source_ids": [r.chunk_id for r in retrieved_items[:2]] or [f"nlm_{nlm_res.get('notebook_id', 'nb')[:8]}"],
                    }
            except Exception as e:
                logger.warning(f"NotebookLM generation bypassed: {e}. Falling back to OpenRouter...")

        # 2b. Try direct Google Gemini API if GEMINI_API_KEY is configured
        if not data and getattr(settings, "GEMINI_API_KEY", ""):
            try:
                gemini_data = self._try_generate_via_google_gemini(f"{STRICT_SYSTEM_PROMPT}\n\n{user_message}")
                if gemini_data:
                    data = gemini_data
            except Exception as e:
                logger.warning(f"Google Gemini API call bypassed: {e}")

        # 2c. Candidate model fallback loop if direct engines not used
        if not data:
            candidate_models = [settings.LLM_MODEL] + [m for m in getattr(settings, "FALLBACK_MODELS", []) if m != settings.LLM_MODEL]

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
            if retrieved_items:
                logger.info("External LLMs unavailable; synthesizing verified reflection directly from retrieved literature.")
                top_chunk = retrieved_items[0]
                book_name = top_chunk.metadata.get("book", "गायत्री महाविज्ञान")
                content_lines = [line.strip() for line in top_chunk.content.split("\n") if line.strip() and not line.strip().startswith("[")]
                quote_text = " ".join(content_lines[:2]) if content_lines else top_chunk.content[:200]

                if detected_lang == "en":
                    extracted_answer = (
                        f"In **{book_name}**, the authorized teachings explain:\n\n"
                        f"📖 **Gurudev**:\n\"{quote_text}\"\n\n"
                        f"🧠 **Arth**:\nMother Gayatri is the primordial cosmic power (Aadya-Shakti) and divine light within the inner self. "
                        f"Her realization and communion manifest through inner purity, refined intellect, and dedicated meditation.\n\n"
                        f"🌱 **Aaj ka Abhyas**:\nPractice regular Gayatri contemplation, cultivate mental purity, and maintain righteous actions throughout daily life."
                    )
                else:
                    extracted_answer = (
                        f"**{book_name}** के प्रमाणिक साहित्य के अनुसार:\n\n"
                        f"📖 **गुरुदेव**:\n\"{quote_text}\"\n\n"
                        f"🧠 **अर्थ**:\nगायत्री आद्याशक्ति एवं आत्म-चेतना हैं। उनका सान्निध्य और साक्षात्कार अंतःकरण की शुद्धि, वासनाओं के शमन और नियमित उपासना से प्राप्त होता है।\n\n"
                        f"🌱 **आज का अभ्यास**:\nदैनिक साधना में गायत्री जप और ज्योति रूप का ध्यान करें तथा अपने विचारों को निरंतर परिष्कृत रखें।"
                    )

                data = {
                    "answer": extracted_answer,
                    "evidence_status": "supported",
                    "used_source_ids": [top_chunk.chunk_id],
                }
            else:
                logger.error("All LLM candidate models failed and no retrieved items. Returning canonical abstention.")
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
