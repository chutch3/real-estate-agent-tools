from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_consumer_session
from backend.container import Container
from backend.exceptions import NetSheetNotFoundError
from backend.models import (
    ConsumerDocumentInfo,
    ConsumerDocumentsResponse,
    ConsumerPropertyResponse,
    NetSheetResponse,
    Representation,
    RepresentationRole,
)
from backend.repositories.document import DocumentRepository
from backend.repositories.properties import PropertyRepository
from backend.repositories.user import UserRepository
from backend.services.net_sheet import NetSheetService

router = APIRouter(prefix="/consumer")


@router.get("/property", status_code=HTTPStatus.OK, response_model=ConsumerPropertyResponse)
@inject
async def get_consumer_property(
    rep: Representation = Depends(get_consumer_session),
    property_repository: PropertyRepository = Depends(Provide[Container.property_repository]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    prop = property_repository.get(rep.property_id)
    agent = user_repository.get_by_id(rep.user_id) if rep.user_id else None

    return ConsumerPropertyResponse(
        address_line1=prop.address_line1,
        address_line2=prop.address_line2,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        square_footage=prop.square_footage,
        year_built=prop.year_built,
        role=rep.role,
        agent_name=agent.name if agent else None,
        agent_email=agent.email if agent else None,
    )


@router.get("/net-sheet", status_code=HTTPStatus.OK, response_model=NetSheetResponse)
@inject
async def get_consumer_net_sheet(
    rep: Representation = Depends(get_consumer_session),
    net_sheet_service: NetSheetService = Depends(Provide[Container.net_sheet_service]),
):
    if rep.role != RepresentationRole.LISTING_AGENT:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Net sheet is only available for sellers")
    try:
        return await net_sheet_service.get_net_sheet(rep.id, rep.brokerage_id)
    except NetSheetNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Net sheet not found")


@router.get("/documents", status_code=HTTPStatus.OK, response_model=ConsumerDocumentsResponse)
@inject
async def get_consumer_documents(
    rep: Representation = Depends(get_consumer_session),
    document_repository: DocumentRepository = Depends(Provide[Container.document_repository]),
):
    all_docs = document_repository.get_by_property_id(rep.property_id)
    visible = [ConsumerDocumentInfo(id=d.id, filename=d.filename) for d in all_docs if d.consumer_visible]
    return ConsumerDocumentsResponse(documents=visible)
