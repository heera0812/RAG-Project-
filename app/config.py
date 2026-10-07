import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    APP_NAME: str = "Shantikunj AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    EXTRACTED_DATA_DIR: Path = BASE_DIR / "data" / "extracted"
    CLEANED_DATA_DIR: Path = BASE_DIR / "data" / "cleaned"
    REVIEW_DATA_DIR: Path = BASE_DIR / "data" / "review"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "data" / "chroma"
    DB_PATH: Path = BASE_DIR / "data" / "shantikunj_metadata.sqlite"

    # API Keys & URLs
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", os.getenv("ANTHROPIC_AUTH_TOKEN", ""))
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")

    # Models
    LLM_MODEL: str = os.getenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")
    OCR_MODEL: str = os.getenv("OCR_MODEL", "google/gemma-4-26b-a4b-it:free")
    FALLBACK_MODELS: list = [
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-24b-instruct-2501:free",
        "google/gemma-4-31b-it:free",
    ]
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    COLLECTION_NAME: str = "shantikunj_authorized_chunks"

    # NotebookLM Integration
    NOTEBOOKLM_ENABLED: bool = os.getenv("NOTEBOOKLM_ENABLED", "true").lower() in ("true", "1")
    NOTEBOOKLM_NOTEBOOK_ID: Optional[str] = os.getenv("NOTEBOOKLM_NOTEBOOK_ID", None)

    # Retrieval Tuning
    RETRIEVAL_CANDIDATES: int = 10
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_HIGH_CONFIDENCE: float = 0.78
    SIMILARITY_MEDIUM_CONFIDENCE: float = 0.65
    SIMILARITY_MIN_THRESHOLD: float = 0.48

    # Chunking Defaults
    CHUNK_TARGET_CHARS: int = 1500
    CHUNK_OVERLAP_CHARS: int = 250
    MIN_CHUNK_CHARS: int = 100

    # Abstention messages per rule 2
    ABSTENTION_HI: str = (
        "वर्तमान में उपलब्ध और प्राप्त प्रमाणित शांतिकुंज ज्ञान-सामग्री में इस प्रश्न "
        "का विश्वसनीय उत्तर देने के लिए पर्याप्त आधार नहीं मिला।"
    )
    ABSTENTION_EN: str = (
        "I could not find sufficient supporting material in the currently indexed "
        "Shantikunj knowledge base to answer this reliably."
    )


settings = Settings()
