from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymilvus.exceptions import MilvusException

from backend.models import ChatMessage
from backend.routes.chat import router
from backend.services.chat import ChatService


class TestChatRoutes:
    def test_chat_streams_assistant_response(self, subject, mock_chat_service):
        mock_chat_service.prepare_chat_messages.return_value = [
            {"role": "user", "content": "Tell me about this property"}
        ]

        async def mock_stream(*args, **kwargs):
            yield "Hello from "
            yield "the assistant"

        mock_chat_service.stream_response.side_effect = mock_stream

        response = subject.post(
            "/properties/prop-1/chat",
            json={"message": "Tell me about this property"},
        )

        assert response.status_code == HTTPStatus.OK
        assert "Hello from " in response.text
        assert "the assistant" in response.text
        mock_chat_service.prepare_chat_messages.assert_awaited_once_with("prop-1", "Tell me about this property")

    def test_chat_returns_503_when_milvus_unavailable(self, subject, mock_chat_service):
        mock_chat_service.prepare_chat_messages.side_effect = MilvusException("connection refused")

        response = subject.post(
            "/properties/prop-1/chat",
            json={"message": "Tell me about this property"},
        )

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    def test_get_chat_history(self, subject, mock_chat_service):
        messages = [
            ChatMessage(
                id="msg-1",
                property_id="prop-1",
                role="user",
                content="Hi",
                created_at="2026-01-01T00:00:00",
            ),
            ChatMessage(
                id="msg-2",
                property_id="prop-1",
                role="assistant",
                content="Hello!",
                created_at="2026-01-01T00:00:01",
            ),
        ]
        mock_chat_service.get_history.return_value = messages

        response = subject.get("/properties/prop-1/chat")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"
        mock_chat_service.get_history.assert_awaited_once_with("prop-1")

    @pytest.fixture
    def mock_chat_service(self):
        yield AsyncMock(spec=ChatService)

    @pytest.fixture
    def subject(self, test_container, mock_chat_service):
        with test_container.override_providers(
            chat_service=mock_chat_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
