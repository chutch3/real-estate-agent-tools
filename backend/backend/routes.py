import logging
from http import HTTPStatus
from http.client import HTTPException
from typing import Annotated, List

from pymilvus.exceptions import MilvusException

from backend.clients.google_maps import GoogleMapsClient
from backend.services.chat import ChatService
from backend.services.document import DocumentService
from backend.services.property import PropertyService
from backend.template_loader import TemplateLoader
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from urllib.parse import unquote_plus

from .container import Container
from .exceptions import (
    AddressNotFoundError,
    DocumentNotFoundError,
    PropertyNotFoundError,
)
from .models import (
    ChatMessageResponse,
    ChatRequest,
    DocumentInfo,
    DocumentUploadResponse,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    PostGenerationResponse,
    PropertyInfo,
    TemplateResponse,
)
from .post_coordinator import PostCoordinator

router = APIRouter()


@router.post("/posts", status_code=HTTPStatus.CREATED)
@inject
async def generate_post(
    request: PostGenerationRequest,
    coordinator: PostCoordinator = Depends(Provide[Container.post_coordinator]),
):
    """
    Generate a post for a property.

    Args:
        request (PostGenerationRequest): The request object.
        coordinator (PostCoordinator): The post coordinator.

    Returns:
        dict: The generated post.
    """
    try:
        post = await coordinator.generate_post(
            address=request.address,
            agent_info=request.agent_info,
            custom_template=request.custom_template,
        )
        return PostGenerationResponse(post=post)
    except PropertyNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Property not found"
        )


@router.post(
    "/geocode",
    status_code=HTTPStatus.CREATED,
    response_model=GeocodeResponse,
)
@inject
async def geocode(
    request: GeocodeRequest,
    google_maps_client: GoogleMapsClient = Depends(
        Provide[Container.google_maps_client]
    ),
):
    """
    Geocode an address.

    Args:
        request (GeocodeRequest): The request object.
        google_maps_client (GoogleMapsClient): The Google Maps client.

    Returns:
        GeocodeResponse: The response object.
    """
    try:
        location = await google_maps_client.geocode(request.address)
        return GeocodeResponse(location=location)
    except AddressNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Address not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unable to geocode address",
        )


@router.get("/templates/default", status_code=HTTPStatus.OK)
@inject
async def get_default_template(
    template_loader: TemplateLoader = Depends(Provide[Container.template_loader]),
):
    """
    Get the default template.

    Args:
        template_loader (TemplateLoader): The template loader.

    Returns:
        TemplateResponse: The response object.
    """
    template = template_loader.read_user_prompt()
    return TemplateResponse(template=template)


@router.post(
    "/documents",
    status_code=HTTPStatus.CREATED,
    response_model=DocumentUploadResponse,
)
@inject
async def upload_pdf(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(Provide[Container.document_service]),
):
    """
    Upload a PDF file.

    Args:
        file (UploadFile): The PDF file.
        address (str): The address.
        document_service (DocumentService): The document service.

    Returns:
        DocumentUploadResponse: The response object.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()
    try:
        doc_id = await document_service.process_pdf(content)
        return DocumentUploadResponse(id=doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.get("/properties/list", status_code=HTTPStatus.OK)
@inject
async def list_properties(
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    return await property_service.list_properties()


@router.get("/properties", status_code=HTTPStatus.OK)
@inject
async def search_properties(
    address: str,
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    """
    Get the property for the given address.

    Args:
        address (str): The address of the property to search for.
        property_service (PropertyService): The property service.

    Returns:
        PropertyInfo: The property details.
    """
    try:
        return await property_service.search_property(
            address=unquote_plus(address),
        )
    except PropertyNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Property not found"
        )
    except Exception as e:
        logging.getLogger(__name__).exception("Error searching property")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unable to get property details",
        )


@router.patch("/properties/{property_id}/documents", status_code=HTTPStatus.OK)
@inject
async def append_document(
    property_id: str,
    document: DocumentInfo,
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    try:
        return await property_service.append_document(property_id, document)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No documents found with the provided IDs",
        )


@router.post("/properties/{property_id}/chat", status_code=HTTPStatus.OK)
@inject
async def chat(
    property_id: str,
    request: ChatRequest,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    try:
        messages = await chat_service.prepare_chat_messages(property_id, request.message)
    except MilvusException:
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Document search unavailable")

    async def event_generator():
        async for chunk in chat_service.stream_response(property_id, messages):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/properties/{property_id}/chat",
    status_code=HTTPStatus.OK,
    response_model=List[ChatMessageResponse],
)
@inject
async def get_chat_history(
    property_id: str,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    return await chat_service.get_history(property_id)


@router.post("/properties", status_code=HTTPStatus.CREATED)
@inject
async def create_property(
    property_data: PropertyInfo,
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    """
    Create a new property.

    Args:
        data (CreatePropertyFormData): The form data.
        property_service (PropertyService): The property service.

    Returns:
        PropertyInfo: The created property.
    """
    try:
        return await property_service.create_property(
            property_data=property_data,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No documents found with the provided IDs",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating property: {str(e)}"
        )
