from typing import List
from fastapi import APIRouter, HTTPException, Path
from app.db.models import DocumentModel, DocumentPageModel
from app.db.repositories import metadata_repo

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=List[DocumentModel])
def list_documents():
    """List all registered and indexed authorized documents."""
    return metadata_repo.list_documents()


@router.get("/{document_id}", response_model=DocumentModel)
def get_document(document_id: str = Path(..., description="Document stable UUID")):
    """Get metadata for a specific document."""
    doc = metadata_repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return doc


@router.get("/{document_id}/pages/{page_number}", response_model=DocumentPageModel)
def get_document_page(
    document_id: str = Path(..., description="Document UUID"),
    page_number: int = Path(..., description="Printed page number"),
):
    """Retrieve full provenance and extracted text for a specific page."""
    page = metadata_repo.get_page(document_id, page_number)
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_number} for document '{document_id}' not found",
        )
    return page
