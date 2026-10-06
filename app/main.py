from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import (
    health_router,
    documents_router,
    search_router,
    chat_router,
    ingest_router,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Source-grounded, multilingual knowledge assistant for verified Shantikunj literature.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
