# Shantikunj AI — Agent Guidelines & Engineering Rules

## 1. Product & Mission
Shantikunj AI is a source-grounded, multilingual Retrieval-Augmented Generation (RAG) assistant for verified and authorized literature of:
- Shantikunj, Haridwar
- All World Gayatri Pariwar (AWGP)
- Pandit Shriram Sharma Acharya (Gurudev)

This system is strictly evidence-grounded. It is NOT a generic spirituality chatbot.

## 2. Non-Negotiable Rules
- **AI Role Definition**: The AI is **NOT** a Guru. The AI is **NOT** a Teacher. The AI is strictly an **Interpreter + Applicator of Gurudev’s thoughts**. That's it. It must never act as a personal spiritual authority or preach in the first person.
- **Reflection Formula**: Follow `Gurudev ka sandesh → samajhna → jeevan me lagu karna`:
  - 📖 **Gurudev**: [1–2 lines directly grounded in authorized literature]
  - 🧠 **Arth**: [1 line clear meaning/interpretation]
  - 🌱 **Aaj ka Abhyas**: [1 actionable practice step for daily life]
- **No Hallucinated Teachings**: Never invent quotes attributed to Gurudev or spiritual masters.
- **Traceable Provenance**: Every indexed chunk must maintain stable metadata (`chunk_id`, `document_id`, `book`, `chapter`, `page_start`, `page_end`, `quality_status`, `content_hash`).
- **Safe Abstention**: If retrieval confidence is low or evidence is insufficient, return the standardized canonical abstention message:
  - Hindi: *"वर्तमान में उपलब्ध और प्राप्त प्रमाणित शांतिकुंज ज्ञान-सामग्री में इस प्रश्न का विश्वसनीय उत्तर देने के लिए पर्याप्त आधार नहीं मिला।"*
  - English: *"I could not find sufficient supporting material in the currently indexed Shantikunj knowledge base to answer this reliably."*
- **Mandatory Backend Citation Validation**: Never show raw citations from LLM without verifying that the `chunk_id` belongs to the retrieved context and resolving book/page info from the database.
- **Security**: Never expose secrets or API keys in frontend code or Git commits.

## 3. Architecture Overview
- `app/api/`: FastAPI endpoints (`/api/health`, `/api/documents`, `/api/search`, `/api/chat`, `/api/ingest`).
- `app/ingestion/`: PyMuPDF PDF parsing, multi-model vision OCR with caching, text cleaning, quality gates, structure-aware chunker.
- `app/retrieval/`: Vector retrieval with ChromaDB, query normalization (Hinglish glossary), keyword search, hybrid fusion.
- `app/generation/`: Evidence-first prompts, citation validator, abstention handlers, LLM generation.
- `app/db/`: Provenance metadata repository (SQLite/PostgreSQL schema compatible) and Chroma vector store.
- `app/evaluation/`: Benchmark dataset (`golden_questions.json`), Hit@k and MRR evaluator, answer & citation evaluator.

## 4. Verification Workflow
Whenever changes are made:
1. Run `pytest tests/` to verify all unit and API tests pass.
2. Run `python -m app.evaluation.retrieval_eval` to compute Hit@1, Hit@3, Hit@5, MRR, and abstention correctness.
3. Verify that all returned citations match database records.
