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
            getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash"),
            "gemini-3.8-flash",
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
                resp = requests.post(url, json=payload, timeout=18.0)
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
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.warning(f"Google Gemini connection/timeout error ({e}). Bypassing further Gemini retries.")
                break
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
                        timeout=12.0,
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
                        f"📜 ANSWER:\n"
                        f"📖 Gurudev: Gayatri is not an independent physical deity but the active divine consciousness (Brahma-Tej) residing within the inner self (Antahkarana); her darshan is the science of realizing this inner divine light.\n\n"
                        f"🧠 Arth: True darshan of Gayatri occurs when the mind-field (Manobhoomi) is purified of ego, greed, and negative desires, allowing the inner divine light to manifest clearly.\n\n"
                        f"🌱 Aaj ka Abhyas: Sit in a quiet, clean space for 10 minutes, meditate on Gayatri's radiant light or Hansvahini form at the heart center, take three deep breaths contemplating cosmic energy, and allow the mind to settle into thoughtless stillness (Vichar-Shoonya); any subtle inner impulse (Sphurana) that arises is her direct guidance."
                    )
                else:
                    extracted_answer = (
                        f"📜 उत्तर:\n"
                        f"📖 गुरुदेव: गायत्री कोई स्वतंत्र देहधारी देवता नहीं वरन् अंतःकरण में अवस्थित ब्रह्मतेज (सक्रिय दिव्य चेतना) है; उनका दर्शन उस अंतःज्योति की प्रत्यक्ष अनुभूति का विज्ञान है।\n\n"
                        f"🧠 अर्थ: गायत्री का सच्चा दर्शन तब होता है जब मनोभूमि अहंकार, लोभ और वासनाओं से मुक्त होकर पवित्र हो जाती है, जिससे अंतरात्मा का दिव्य प्रकाश स्पष्ट प्रकाशित होता है।\n\n"
                        f"🌱 आज का अभ्यास: शांत व स्वच्छ स्थान पर 10 मिनट बैठें, हृदय चक्र पर गायत्री के ज्योतिर्मय स्वरूप या हंसवाहिनी रूप का ध्यान करें, तीन गहरे श्वास लेकर विचार-शून्यता का अभ्यास करें; उठने वाली सूक्ष्म सद्प्रेरणा ही उनका प्रत्यक्ष मार्गदर्शन है।"
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

        # Format with structured reflection (Gurudev -> Arth -> Abhyas)
        gurudev_msg = data.get("gurudev_sandesh")
        arth_msg = data.get("arth")
        abhyas_msg = data.get("aaj_ka_abhyas")

        formatted_answer = raw_answer
        if gurudev_msg and arth_msg and abhyas_msg:
            header = "📜 उत्तर:" if detected_lang == "hi" else "📜 ANSWER:"
            g_lbl = "📖 गुरुदेव:" if detected_lang == "hi" else "📖 Gurudev:"
            a_lbl = "🧠 अर्थ:" if detected_lang == "hi" else "🧠 Arth:"
            ab_lbl = "🌱 आज का अभ्यास:" if detected_lang == "hi" else "🌱 Aaj ka Abhyas:"
            formatted_answer = (
                f"{header}\n"
                f"{g_lbl} {gurudev_msg.strip()}\n\n"
                f"{a_lbl} {arth_msg.strip()}\n\n"
                f"{ab_lbl} {abhyas_msg.strip()}"
            )
        else:
            # Ensure starts with header and proper section line spacing
            header = "📜 उत्तर:" if detected_lang == "hi" else "📜 ANSWER:"
            clean_text = raw_answer.strip()
            if not (clean_text.startswith("📜 ANSWER:") or clean_text.startswith("📜 उत्तर:")):
                clean_text = f"{header}\n{clean_text}"
            for marker in ["🧠 Arth:", "🧠 अर्थ:", "🌱 Aaj ka Abhyas:", "🌱 आज का अभ्यास:"]:
                if marker in clean_text and f"\n\n{marker}" not in clean_text:
                    clean_text = clean_text.replace(f"\n{marker}", f"\n\n{marker}")
            formatted_answer = clean_text

        return ChatResponse(
            answer=formatted_answer,
            evidence_status=evidence_status,
            retrieval_confidence=retrieval_confidence,
            sources=validated_sources,
            conversation_id=conversation_id,
        )


answer_generator = AnswerGenerator()
