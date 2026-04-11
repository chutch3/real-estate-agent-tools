from datetime import UTC, datetime, timedelta

from dependency_injector.wiring import Provide, inject
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from backend.container import Container
from backend.services.security import SecurityService


class SlidingTokenRefreshMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    @inject
    async def dispatch(
        self,
        request: Request,
        call_next,
        security_service: SecurityService = Provide[Container.security_service],
    ) -> Response:
        response = await call_next(request)
        token = request.cookies.get("access_token")
        if token:
            try:
                claims = security_service.decode_token(token)
                exp_ts = claims.get("exp")
                if exp_ts is None:
                    return response
                exp = datetime.fromtimestamp(exp_ts, tz=UTC)
                remaining = exp - datetime.now(UTC)
                threshold = timedelta(minutes=security_service.token_expire_minutes // 2)
                if remaining < threshold:
                    new_token = security_service.create_access_token(
                        user_id=claims["sub"],
                        brokerage_id=claims["org"],
                        role=claims["role"],
                    )
                    response.set_cookie(
                        "access_token",
                        new_token,
                        httponly=True,
                        samesite="lax",
                        secure=False,
                    )
            except JWTError:
                pass
        return response
