"""Internal service entrypoint for rag-for-beginners."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAG for Beginners (Internal Service)",
    version="1.0.0",
    description="Internal educational pipeline and experimentation service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "rag-for-beginners",
        "status": "online",
        "type": "internal_service",
        "description": "Educational RAG pipelines, chunking experiments, and tutorial benchmarks.",
    }


@app.get("/health")
def health():
    return {
        "service": "rag-for-beginners",
        "status": "healthy",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
