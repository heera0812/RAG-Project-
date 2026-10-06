import os
import time
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from openai import OpenAI

from app.config import settings
from app.ingestion.quality_checks import QualityChecker
from app.ingestion.cleaner import clean_hindi_text

logger = logging.getLogger(__name__)


class OCREngine:
    """High-fidelity Devanagari OCR engine with caching, multi-model fallback, and quality gates."""

    def __init__(self):
        self.cache_dir = Path(settings.EXTRACTED_DATA_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir = Path(settings.REVIEW_DATA_DIR)
        self.review_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.primary_model = settings.OCR_MODEL

        # Priority fallback chain of vision models
        self.fallback_models = [
            "google/gemma-4-31b-it:free",
            "qwen/qwen3.8-27b:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "google/gemma-4-26b-a4b-it:free",
        ]
        if self.primary_model not in self.fallback_models:
            self.fallback_models.insert(0, self.primary_model)

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or "dummy_key",
        )

    def _get_cache_path(self, doc_slug: str, page_number: int) -> Path:
        return self.cache_dir / f"{doc_slug}_p{page_number:04d}.json"

    def extract_page_ocr(
        self,
        image_bytes: bytes,
        doc_slug: str,
        page_number: int,
        use_cache: bool = True,
    ) -> Tuple[str, float, bool, Optional[str]]:
        """Extract text from a page image using vision model with fallback.

        Returns: (raw_text, confidence, has_issues, issue_reason)
        """
        cache_path = self._get_cache_path(doc_slug, page_number)
        if use_cache and cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("raw_text") and len(data["raw_text"]) > 40:
                        return (
                            data["raw_text"],
                            float(data.get("confidence", 1.0)),
                            bool(data.get("has_issues", False)),
                            data.get("issue_reason"),
                        )
            except Exception:
                pass

        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "You are a high-precision Devanagari Hindi OCR engine. "
            "Accurately transcribe all Hindi/Sanskrit text from this book page into Devanagari Unicode. "
            "Preserve paragraphs, section headings, and exact words. "
            "Do not add any commentary, translations, explanations, or notes. "
            "Output ONLY the transcribed text."
        )

        raw_text = ""
        last_error = ""

        # Try models in fallback sequence with backoff
        for model_name in self.fallback_models:
            for attempt in range(2):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Transcribe this Hindi page into Devanagari text:"},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{b64_image}"
                                        },
                                    },
                                ],
                            },
                        ],
                        temperature=0.0,
                        max_tokens=1800,
                        timeout=35,
                    )
                    candidate_text = (response.choices[0].message.content or "").strip()
                    if len(candidate_text) > 40:
                        raw_text = candidate_text
                        break
                except Exception as e:
                    last_error = str(e)
                    time.sleep(2)
            if raw_text:
                break

        if not raw_text:
            has_issues = True
            issue_reason = f"OCR failed across all fallback models: {last_error}"
            return "", 0.0, has_issues, issue_reason

        # Run quality check
        is_valid, issue = QualityChecker.check_page_text(raw_text)
        confidence = 0.95 if is_valid else 0.40
        has_issues = not is_valid
        issue_reason = issue

        # Save to cache
        cache_data = {
            "doc_slug": doc_slug,
            "page_number": page_number,
            "raw_text": raw_text,
            "cleaned_text": clean_hindi_text(raw_text),
            "confidence": confidence,
            "has_issues": has_issues,
            "issue_reason": issue_reason,
        }
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        if has_issues:
            review_file = self.review_dir / f"{doc_slug}_p{page_number:04d}_flagged.json"
            with open(review_file, "w", encoding="utf-8") as rf:
                json.dump(cache_data, rf, ensure_ascii=False, indent=2)

        return raw_text, confidence, has_issues, issue_reason


ocr_engine = OCREngine()
