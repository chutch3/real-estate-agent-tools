from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import InvalidAccessError
from backend.models import (
    AccessCodeResponse,
    ConsumerSessionRequest,
    ConsumerSessionResponse,
    PortalInfoResponse,
    User,
)
from backend.repositories.properties import PropertyRepository
from backend.repositories.representation import RepresentationRepository
from backend.services.access_code import AccessCodeService
from backend.services.rate_limiter import RateLimiter

router = APIRouter()


@router.post(
    "/representations/{representation_id}/access-code",
    status_code=HTTPStatus.CREATED,
    response_model=AccessCodeResponse,
)
@inject
async def generate_access_code(
    representation_id: str,
    current_user: User = Depends(get_current_user),
    access_code_service: AccessCodeService = Depends(Provide[Container.access_code_service]),
    representation_repository: RepresentationRepository = Depends(Provide[Container.representation_repository]),
    portal_base_url: str = Depends(Provide[Container.config.portal.base_url]),
):
    try:
        code = access_code_service.generate(representation_id, current_user.brokerage_id)
    except InvalidAccessError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Representation not found")
    rep = representation_repository.get(representation_id)
    return AccessCodeResponse(
        code=code,
        portal_url=f"{portal_base_url}/portal/{rep.portal_token}",
    )


@router.get(
    "/representations/{representation_id}/portal",
    status_code=HTTPStatus.OK,
    response_model=PortalInfoResponse,
)
@inject
async def get_portal_info(
    representation_id: str,
    current_user: User = Depends(get_current_user),
    access_code_service: AccessCodeService = Depends(Provide[Container.access_code_service]),
    representation_repository: RepresentationRepository = Depends(Provide[Container.representation_repository]),
    portal_base_url: str = Depends(Provide[Container.config.portal.base_url]),
):
    try:
        has_code = access_code_service.has_active_code(representation_id, current_user.brokerage_id)
    except InvalidAccessError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Representation not found")
    rep = representation_repository.get(representation_id)
    return PortalInfoResponse(
        portal_url=f"{portal_base_url}/portal/{rep.portal_token}",
        has_active_code=has_code,
    )


@router.post(
    "/portal/{portal_token}/session",
    status_code=HTTPStatus.OK,
    response_model=ConsumerSessionResponse,
)
@inject
async def create_consumer_session(
    portal_token: str,
    body: ConsumerSessionRequest,
    request: Request,
    response: Response,
    access_code_service: AccessCodeService = Depends(Provide[Container.access_code_service]),
    property_repository: PropertyRepository = Depends(Provide[Container.property_repository]),
    rate_limiter: RateLimiter = Depends(Provide[Container.rate_limiter]),
):
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    if not rate_limiter.is_allowed(f"portal_session:{client_ip}"):
        raise HTTPException(status_code=HTTPStatus.TOO_MANY_REQUESTS, detail="Too many requests")

    try:
        rep = access_code_service.validate(portal_token, body.code)
    except InvalidAccessError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid portal token or access code")

    prop = property_repository.get(rep.property_id)
    parts = [p for p in [prop.address_line1, prop.city, prop.state, prop.zip_code] if p]
    property_address = ", ".join(parts) if parts else None

    response.set_cookie(
        key="consumer_token",
        value=rep.portal_token,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return ConsumerSessionResponse(
        representation_id=rep.id,
        role=rep.role,
        property_address=property_address,
    )
