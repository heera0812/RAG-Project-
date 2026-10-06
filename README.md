# Shantikunj AI

A source-grounded, multilingual Retrieval-Augmented Generation (RAG) knowledge assistant for the verified and authorized literature of **Shantikunj, Gayatri Pariwar, and Pandit Shriram Sharma Acharya**.

---

## Key Principles & Architectural Guarantees

1. **Evidence-First Grounding**: Answers are synthesized strictly from retrieved and authorized literature. If supporting material is absent, the system safely abstains rather than hallucinating answers from general model memory.
2. **Page-Level Provenance**: Every knowledge chunk retains complete provenance metadata:
   - Book title, Chapter, Section
   - `page_start` and `page_end` (spans accurately recorded)
   - SHA-256 Content Hash, Document ID, and Stable Chunk UUID
   - Extraction method (`pdf_text` or `ocr`), confidence score, and quality status
3. **Mandatory Backend Citation Validation**: Citations returned to users are strictly verified by backend logic against the retrieved context and resolved directly from persistent database records.
4. **Hinglish & Multilingual Retrieval**: Supports Hindi, English, and Hinglish queries via conceptual glossary normalization and hybrid retrieval.
5. **Quality Gated Ingestion**: All pages and chunks pass automated quality gates (Unicode sanity checks, OCR garbage detection, length thresholds).

---

## Project Structure

```text
shantikunj_ai/
├── AGENTS.md                  # Development guidelines and agent rules
├── README.md                  # System overview and quick start guide
├── .env.example               # Environment variables template
├── requirements.txt           # Project dependencies
│
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Configuration & thresholds
│   │
│   ├── api/                   # REST API routes
│   │   ├── health.py          # GET  /api/health
│   │   ├── documents.py       # GET  /api/documents, /api/documents/{id}/pages/{page}
│   │   ├── search.py          # POST /api/search
│   │   ├── chat.py            # POST /api/chat
│   │   └── ingest.py          # POST /api/ingest
│   │
│   ├── ingestion/             # Ingestion & OCR pipeline
│   │   ├── pdf_parser.py      # PyMuPDF extraction orchestrator
│   │   ├── ocr.py             # Vision OCR with multi-model fallback & caching
│   │   ├── cleaner.py         # Devanagari text cleaner & normalizer
│   │   ├── language.py        # Language & script detector
│   │   ├── quality_checks.py  # Page & chunk quality gates
│   │   └── chunker.py         # Structure-aware chunker
│   │
│   ├── retrieval/             # Search & ranking
│   │   ├── query_normalizer.py# Hinglish glossary expansion
│   │   ├── vector_search.py   # ChromaDB vector retrieval & confidence
│   │   ├── keyword_search.py  # Lexical matcher
│   │   └── hybrid_search.py   # Hybrid fusion
│   │
│   ├── generation/            # Evidence-grounded generation
│   │   ├── prompts.py         # Strict system prompt & context formatter
│   │   ├── citation_validator.py # Backend citation verification
│   │   ├── abstention.py      # Non-negotiable abstention messages
│   │   └── answer_generator.py# LLM caller & coordinator
│   │
│   ├── db/                    # Persistent storage
│   │   ├── models.py          # Pydantic data schemas
│   │   └── repositories.py    # SQLite provenance & Chroma vector store
│   │
│   └── evaluation/            # Automated evaluation framework
│       ├── golden_questions.json # 25+ benchmark golden questions
│       ├── retrieval_eval.py  # Hit@1, Hit@3, Hit@5, MRR evaluator
│       └── answer_eval.py     # End-to-end faithfulness evaluator
│
├── data/                      # Data directories
│   ├── raw/                   # Original authorized PDFs
│   ├── extracted/             # Cached page-by-page extractions
│   ├── cleaned/               # Normalized text files
│   ├── review/                # Flagged low-confidence pages
│   └── chroma/                # ChromaDB vector index
│
└── tests/                     # Automated unit and integration test suite
```

---

## Installation & Setup

1. **Clone repository & activate virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and provide your keys:
   ```bash
   cp .env.example .env
   ```

4. **Run Unit Tests**:
   ```bash
   pytest tests/
   ```

5. **Run Master Test Cases Evaluation (105 Canonical Cases)**:
   ```bash
   python -m app.evaluation.master_testcase_eval
   ```

6. **Interactive Terminal Q&A (Ask Questions directly)**:
   - **Interactive Mode**:
     ```bash
     python -m app.cli
     ```
   - **One-off Question**:
     ```bash
     python -m app.cli "गायत्री महाविज्ञान"
     ```

7. **Start FastAPI Server**:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## API Endpoints

- `GET  /api/health`: System health and indexing counts.
- `GET  /api/documents`: List authorized indexed documents.
- `GET  /api/documents/{id}/pages/{page}`: Inspect extracted text and provenance for a printed page.
- `POST /api/search`: Query chunks with vector or hybrid search.
- `POST /api/chat`: Evidence-grounded Q&A with citation verification.
- `POST /api/ingest`: Trigger document ingestion.
