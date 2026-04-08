from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import Cookie, Depends, HTTPException
from jose import JWTError

from backend.container import Container
from backend.models import User
from backend.repositories.user import UserRepository
from backend.services.security import SecurityService


@inject
def get_current_user(
    access_token: str | None = Cookie(default=None),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
) -> User:
    if access_token is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Not authenticated")
    try:
        claims = security_service.decode_token(access_token)
    except JWTError:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid or expired token")
    user = user_repository.get_by_id(claims["sub"])
    if user is None:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="User not found")
    return user
