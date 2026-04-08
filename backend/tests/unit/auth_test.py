from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from jose import JWTError

from backend.auth import get_current_user
from backend.models import User
from backend.repositories.user import UserRepository
from backend.services.security import SecurityService


def test_get_current_user_raises_401_when_no_token():
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_security_service = MagicMock(spec=SecurityService)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            access_token=None,
            user_repository=mock_user_repo,
            security_service=mock_security_service,
        )

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"


def test_get_current_user_raises_401_when_token_invalid():
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_security_service = MagicMock(spec=SecurityService)
    mock_security_service.decode_token.side_effect = JWTError("invalid token")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            access_token="invalid_token",
            user_repository=mock_user_repo,
            security_service=mock_security_service,
        )

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired token"
    mock_security_service.decode_token.assert_called_once_with("invalid_token")


def test_get_current_user_raises_401_when_user_not_found():
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_security_service = MagicMock(spec=SecurityService)
    mock_security_service.decode_token.return_value = {"sub": "user-123"}
    mock_user_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            access_token="valid_token_missing_user",
            user_repository=mock_user_repo,
            security_service=mock_security_service,
        )

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == "User not found"
    mock_security_service.decode_token.assert_called_once_with("valid_token_missing_user")
    mock_user_repo.get_by_id.assert_called_once_with("user-123")


def test_get_current_user_returns_user_when_valid():
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_security_service = MagicMock(spec=SecurityService)
    mock_security_service.decode_token.return_value = {"sub": "user-123"}
    expected_user = User(id="user-123", email="test@test.com", role="AGENT", brokerage_id="brokerage-1")
    mock_user_repo.get_by_id.return_value = expected_user

    actual_user = get_current_user(
        access_token="valid_token",
        user_repository=mock_user_repo,
        security_service=mock_security_service,
    )

    assert actual_user == expected_user
    mock_security_service.decode_token.assert_called_once_with("valid_token")
    mock_user_repo.get_by_id.assert_called_once_with("user-123")
