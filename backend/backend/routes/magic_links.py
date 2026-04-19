from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import InvalidMagicLinkError
from backend.models import (
    ConsumerSessionResponse,
    MagicLinkListResponse,
    MagicLinkResponse,
    User,
)
from backend.repositories.properties import PropertyRepository
from backend.repositories.representation import RepresentationRepository
from backend.services.magic_link import MagicLinkService
from backend.services.rate_limiter import RateLimiter

router = APIRouter()


def _to_response(token) -> MagicLinkResponse:
    return MagicLinkResponse(
        id=token.id,
        token=token.token,
        expires_at=token.expires_at,
        last_accessed_at=token.last_accessed_at,
    )


@router.post(
    "/representations/{representation_id}/magic-links",
    status_code=HTTPStatus.CREATED,
    response_model=MagicLinkResponse,
)
@inject
async def create_magic_link(
    representation_id: str,
    current_user: User = Depends(get_current_user),
    magic_link_service: MagicLinkService = Depends(Provide[Container.magic_link_service]),
):
    try:
        token = magic_link_service.create_magic_link(representation_id, current_user.brokerage_id)
        return _to_response(token)
    except InvalidMagicLinkError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Representation not found")


@router.get(
    "/representations/{representation_id}/magic-links",
    status_code=HTTPStatus.OK,
    response_model=MagicLinkListResponse,
)
@inject
async def list_magic_links(
    representation_id: str,
    current_user: User = Depends(get_current_user),
    magic_link_service: MagicLinkService = Depends(Provide[Container.magic_link_service]),
):
    try:
        tokens = magic_link_service.list_tokens(representation_id, current_user.brokerage_id)
        return MagicLinkListResponse(tokens=[_to_response(t) for t in tokens])
    except InvalidMagicLinkError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Representation not found")


@router.delete(
    "/representations/{representation_id}/magic-links/{token_id}",
    status_code=HTTPStatus.NO_CONTENT,
)
@inject
async def revoke_magic_link(
    representation_id: str,
    token_id: str,
    current_user: User = Depends(get_current_user),
    magic_link_service: MagicLinkService = Depends(Provide[Container.magic_link_service]),
):
    try:
        magic_link_service.revoke_token(token_id, current_user.brokerage_id)
    except InvalidMagicLinkError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Token not found")


@router.post(
    "/magic/{token}/session",
    status_code=HTTPStatus.OK,
    response_model=ConsumerSessionResponse,
)
@inject
async def create_consumer_session(
    token: str,
    request: Request,
    response: Response,
    magic_link_service: MagicLinkService = Depends(Provide[Container.magic_link_service]),
    representation_repository: RepresentationRepository = Depends(Provide[Container.representation_repository]),
    property_repository: PropertyRepository = Depends(Provide[Container.property_repository]),
    rate_limiter: RateLimiter = Depends(Provide[Container.rate_limiter]),
):
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    if not rate_limiter.is_allowed(f"magic_session:{client_ip}"):
        raise HTTPException(status_code=HTTPStatus.TOO_MANY_REQUESTS, detail="Too many requests")

    try:
        link = magic_link_service.validate_token(token)
    except InvalidMagicLinkError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid or expired link")

    rep = representation_repository.get(link.representation_id)
    prop = property_repository.get(rep.property_id)

    parts = [p for p in [prop.address_line1, prop.city, prop.state, prop.zip_code] if p]
    property_address = ", ".join(parts) if parts else None

    response.set_cookie(
        key="consumer_token",
        value=link.token,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return ConsumerSessionResponse(
        representation_id=rep.id,
        role=rep.role,
        property_address=property_address,
    )
