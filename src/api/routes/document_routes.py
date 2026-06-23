import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.core.deps import get_embedding_service, get_document_repo
from src.api.schemas.document_schema import DocumentResponse
from src.infrastructure.extractors.extractor_router import SUPPORTED_EXTENSIONS
from src.infrastructure.db.document_repository import ImpDocumentRepository
from src.infrastructure.embedding.embedding_repository import ImpEmbeddingRepository
from src.use_cases.ingest_document_usecase import IngestDocumentUseCase

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
    "application/octet-stream",
}

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    repo: ImpDocumentRepository = Depends(get_document_repo),
    embedding_service: ImpEmbeddingRepository = Depends(get_embedding_service),
):
    file_name = file.filename or "unnamed"
    ext = os.path.splitext(file_name)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        use_case = IngestDocumentUseCase(repo, embedding_service)
        document = await use_case.execute(tmp_path, file_name)
    finally:
        os.unlink(tmp_path)

    return DocumentResponse(
        id=document.id,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size=document.file_size,
        ingested_at=document.ingested_at,
        chunk_count=document.chunk_count,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    repo: ImpDocumentRepository = Depends(get_document_repo),
):
    docs = await repo.list_documents()
    return [
        DocumentResponse(
            id=d.id,
            file_name=d.file_name,
            file_type=d.file_type,
            file_size=d.file_size,
            ingested_at=d.ingested_at,
            chunk_count=d.chunk_count,
        )
        for d in docs
    ]
    
@router.delete("", status_code=200)
async def delete_all_docs(
    repo: ImpDocumentRepository = Depends(get_document_repo),
):
    try:
        await repo.delete_all_documents()
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    repo: ImpDocumentRepository = Depends(get_document_repo),
):
    doc = await repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await repo.delete_document(document_id)
    

    # await repo.delete_document(document_id)