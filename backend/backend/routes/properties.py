import logging
from http import HTTPStatus
from urllib.parse import unquote_plus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import (
    DocumentNotFoundError,
    DualAgencyNotAllowedError,
    PropertyNotFoundError,
)
from backend.models import DocumentInfo, PropertyInfo, User
from backend.services.property import PropertyService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/properties/list", status_code=HTTPStatus.OK)
@inject
async def list_properties(
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    return await property_service.list_properties(brokerage_id=current_user.brokerage_id)


@router.get("/properties", status_code=HTTPStatus.OK)
@inject
async def search_properties(
    address: str,
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    try:
        return await property_service.search_property(address=unquote_plus(address))
    except PropertyNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")
    except Exception:
        logger.exception("Error searching property")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unable to get property details",
        )


@router.post("/properties", status_code=HTTPStatus.CREATED)
@inject
async def create_property(
    property_data: PropertyInfo,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    try:
        return await property_service.create_property(
            property_data=property_data,
            brokerage_id=current_user.brokerage_id,
        )
    except DualAgencyNotAllowedError:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Dual agency is not permitted for this brokerage",
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No documents found with the provided IDs",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating property: {str(e)}")


@router.delete("/properties/{property_id}/documents/{doc_id}", status_code=HTTPStatus.OK)
@inject
async def delete_document(
    property_id: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    try:
        return await property_service.remove_document(property_id, doc_id, brokerage_id=current_user.brokerage_id)
    except PropertyNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")
    except DocumentNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Document not found")


@router.patch("/properties/{property_id}/documents", status_code=HTTPStatus.OK)
@inject
async def append_document(
    property_id: str,
    document: DocumentInfo,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    try:
        return await property_service.append_document(property_id, document, brokerage_id=current_user.brokerage_id)
    except PropertyNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No documents found with the provided IDs",
        )
