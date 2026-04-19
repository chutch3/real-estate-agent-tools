import asyncio
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import DocumentNotFoundError
from backend.models import DocumentUploadResponse, DocumentVisibilityResponse, DocumentVisibilityUpdate, User
from backend.repositories.document import DocumentRepository
from backend.repositories.document_storage import DocumentStorageRepository
from backend.repositories.representation import RepresentationRepository
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


@router.patch(
    "/properties/{property_id}/documents/{document_id}/visibility",
    status_code=HTTPStatus.OK,
    response_model=DocumentVisibilityResponse,
)
@inject
async def update_document_visibility(
    property_id: str,
    document_id: str,
    update: DocumentVisibilityUpdate,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(Provide[Container.document_repository]),
    representation_repository: RepresentationRepository = Depends(Provide[Container.representation_repository]),
):
    reps = representation_repository.list_with_property(current_user.brokerage_id)
    property_ids = {p.id for _, p in reps}
    if property_id not in property_ids:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")

    existing = document_repository.get_by_id(document_id)
    if existing is None or existing.property_id != property_id:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Document not found")

    doc = document_repository.update_visibility(document_id, update.consumer_visible)
    if doc is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Document not found")

    return DocumentVisibilityResponse(
        id=doc.id,
        filename=doc.filename,
        consumer_visible=doc.consumer_visible,
    )
