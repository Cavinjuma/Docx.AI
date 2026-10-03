from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUserDep, SessionDep
from app.ingestion import chunk_text, extract_text
from app.models import Document, DocumentChunk
from app.schemas.document import DocumentUploadResponse

router = APIRouter(tags=["documents"])
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: Annotated[UploadFile, File(...)],
    db: SessionDep,
    current_user: CurrentUserDep,
) -> DocumentUploadResponse:
    """Persist metadata for a newly uploaded file and return the stored record."""
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, DOCX, TXT, Markdown.",
        )

    contents = file.file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content cannot be empty",
        )

    try:
        extracted_text = extract_text(contents, suffix)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_type=suffix.lstrip("."),
        file_size=len(contents),
        processing_status="PROCESSED",
    )
    db.add(document)
    db.flush()

    db.add_all(
        DocumentChunk(
            document_id=document.id,
            chunk_text=text,
            chunk_index=index,
            chunk_metadata={"source": document.filename},
        )
        for index, text in enumerate(chunk_text(extracted_text))
    )
    db.commit()
    db.refresh(document)

    return DocumentUploadResponse(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        upload_date=document.upload_date,
        processing_status=document.processing_status,
    )
