from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from backend.container import Container
from backend.models import (
    Brokerage,
    BrokerageCreate,
    BrokerageResponse,
    MeResponse,
    TokenResponse,
    User,
    UserCreate,
    UserResponse,
)
from backend.repositories.brokerage import BrokerageRepository
from backend.repositories.user import UserRepository
from backend.services.security import SecurityService

_COOKIE_NAME = "access_token"

router = APIRouter()


@router.post("/brokerages", status_code=HTTPStatus.CREATED)
@inject
def create_brokerage(
    payload: BrokerageCreate,
    brokerage_repository: BrokerageRepository = Depends(Provide[Container.brokerage_repository]),
) -> BrokerageResponse:
    brokerage = Brokerage(name=payload.name, contact_info=payload.contact_info)
    created = brokerage_repository.create(brokerage)
    return BrokerageResponse(id=created.id, name=created.name, contact_info=created.contact_info)


@router.post("/users", status_code=HTTPStatus.CREATED)
@inject
def create_user(
    payload: UserCreate,
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
) -> UserResponse:
    hashed = security_service.hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed, role=payload.role, brokerage_id=payload.brokerage_id)
    created = user_repository.create(user)
    return UserResponse(id=created.id, email=created.email, role=created.role, brokerage_id=created.brokerage_id)


@router.post("/auth/token")
@inject
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
) -> TokenResponse:
    user = user_repository.get_by_email(form_data.username)
    if user is None or not security_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Incorrect email or password")
    token = security_service.create_access_token(user_id=user.id, brokerage_id=user.brokerage_id, role=user.role)
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return TokenResponse()


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(key=_COOKIE_NAME, httponly=True, samesite="lax")
    return {"message": "logged out"}


@router.get("/users/me")
@inject
def get_me(
    access_token: str | None = Cookie(default=None),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    brokerage_repository: BrokerageRepository = Depends(Provide[Container.brokerage_repository]),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
) -> MeResponse:
    if access_token is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Not authenticated")
    try:
        claims = security_service.decode_token(access_token)
    except JWTError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid or expired token")
    user = user_repository.get_by_id(claims["sub"])
    if user is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="User not found")
    brokerage = brokerage_repository.get_by_id(user.brokerage_id)
    return MeResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        brokerage_id=user.brokerage_id,
        brokerage=BrokerageResponse(id=brokerage.id, name=brokerage.name, contact_info=brokerage.contact_info),
    )
