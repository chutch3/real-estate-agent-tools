import asyncio
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from backend.container import Container
from backend.exceptions import DocumentNotFoundError
from backend.models import DocumentUploadResponse
from backend.repositories.document_storage import DocumentStorageRepository
from backend.services.document import DocumentService

router = APIRouter()


@router.get("/documents/{doc_id}", status_code=HTTPStatus.OK)
@inject
async def get_document(
    doc_id: str,
    document_storage_repository: DocumentStorageRepository = Depends(Provide[Container.document_storage_repository]),
):
    try:
        content = await asyncio.to_thread(document_storage_repository.get, doc_id)
        return Response(content=content, media_type="application/pdf")
    except DocumentNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Document not found")


@router.post("/documents", status_code=HTTPStatus.CREATED, response_model=DocumentUploadResponse)
@inject
async def upload_pdf(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(Provide[Container.document_service]),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()
    try:
        doc_id = await document_service.process_pdf(content)
        return DocumentUploadResponse(id=doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
