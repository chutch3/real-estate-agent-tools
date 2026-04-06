from unittest.mock import AsyncMock, MagicMock

import pytest
from pymilvus.exceptions import MilvusException

from backend.clients.openai import OpenAIClient
from backend.models import ChatMessage, PropertyInfo
from backend.repositories.chat_messages import ChatMessageRepository
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.repositories.properties import PropertyRepository
from backend.services.chat import ChatService


class TestChatService:
    @pytest.mark.asyncio
    async def test_prepare_chat_messages_saves_user_message(
        self, subject, mock_chat_message_repository, mock_property_repository, mock_openai_client
    ):
        mock_property_repository.get_property.return_value = PropertyInfo(id="prop-1", latitude=37.4, longitude=-122.0)
        mock_openai_client.create_embeddings.return_value = [0.1] * 1536
        mock_chat_message_repository.get_history.return_value = []

        await subject.prepare_chat_messages("prop-1", "Tell me about this property")

        mock_chat_message_repository.save_message.assert_awaited_once_with(
            "prop-1", "user", "Tell me about this property"
        )

    @pytest.mark.asyncio
    async def test_prepare_chat_messages_filters_rag_by_property_doc_ids(
        self,
        subject,
        mock_chat_message_repository,
        mock_property_repository,
        mock_openai_client,
        mock_document_embedding_repository,
    ):
        mock_property_repository.get_property.return_value = PropertyInfo(
            id="prop-1",
            latitude=37.4,
            longitude=-122.0,
            documents=[MagicMock(id="doc-1"), MagicMock(id="doc-2")],
        )
        mock_openai_client.create_embeddings.return_value = [0.1] * 1536
        mock_document_embedding_repository.query_embeddings.return_value = []
        mock_chat_message_repository.get_history.return_value = []

        await subject.prepare_chat_messages("prop-1", "Hi")

        call_kwargs = mock_document_embedding_repository.query_embeddings.call_args.kwargs
        assert call_kwargs["filter_ids"] == ["doc-1", "doc-2"]

    @pytest.mark.asyncio
    async def test_prepare_chat_messages_does_not_filter_rag_when_no_documents(
        self,
        subject,
        mock_chat_message_repository,
        mock_property_repository,
        mock_openai_client,
        mock_document_embedding_repository,
    ):
        mock_property_repository.get_property.return_value = PropertyInfo(
            id="prop-1", latitude=37.4, longitude=-122.0, documents=None
        )
        mock_openai_client.create_embeddings.return_value = [0.1] * 1536
        mock_document_embedding_repository.query_embeddings.return_value = []
        mock_chat_message_repository.get_history.return_value = []

        await subject.prepare_chat_messages("prop-1", "Hi")

        call_kwargs = mock_document_embedding_repository.query_embeddings.call_args.kwargs
        assert call_kwargs["filter_ids"] is None

    @pytest.mark.asyncio
    async def test_prepare_chat_messages_raises_when_milvus_unavailable(
        self,
        subject,
        mock_chat_message_repository,
        mock_property_repository,
        mock_openai_client,
        mock_document_embedding_repository,
    ):
        mock_property_repository.get_property.return_value = PropertyInfo(id="prop-1", latitude=37.4, longitude=-122.0)
        mock_openai_client.create_embeddings.return_value = [0.1] * 1536
        mock_document_embedding_repository.query_embeddings.side_effect = MilvusException("connection refused")

        with pytest.raises(MilvusException):
            await subject.prepare_chat_messages("prop-1", "Hi")

    @pytest.mark.asyncio
    async def test_stream_response_yields_chunks_and_saves_assistant_message(
        self, subject, mock_chat_message_repository, mock_openai_client
    ):
        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "World"

        mock_openai_client.stream_completion.side_effect = mock_stream

        messages = [{"role": "user", "content": "Hi"}]
        chunks = [chunk async for chunk in subject.stream_response("prop-1", messages)]

        assert chunks == ["Hello ", "World"]
        mock_chat_message_repository.save_message.assert_awaited_once_with("prop-1", "assistant", "Hello World")

    @pytest.mark.asyncio
    async def test_stream_response_passes_max_tokens_to_stream_completion(
        self, subject, mock_chat_message_repository, mock_openai_client
    ):
        async def mock_stream(*args, **kwargs):
            yield "response"

        mock_openai_client.stream_completion.side_effect = mock_stream

        messages = [{"role": "user", "content": "Hi"}]
        [chunk async for chunk in subject.stream_response("prop-1", messages)]

        call_kwargs = mock_openai_client.stream_completion.call_args.kwargs
        assert call_kwargs.get("max_tokens") == 500

    @pytest.mark.asyncio
    async def test_get_history_returns_messages_for_property(self, subject, mock_chat_message_repository):
        messages = [
            ChatMessage(
                id="msg-1",
                property_id="prop-1",
                role="user",
                content="Hi",
                created_at="2026-01-01T00:00:00",
            ),
        ]
        mock_chat_message_repository.get_history.return_value = messages

        result = await subject.get_history("prop-1")

        assert result == messages
        mock_chat_message_repository.get_history.assert_awaited_once_with("prop-1")

    def test_build_system_prompt_includes_rag_results(self, subject):
        property_info = PropertyInfo(id="prop-1", formatted_address="123 Main St", city="Sellersburg", state="IN")
        rag_results = [
            {"text": "The purchase agreement states a price of $300k."},
            {"text": "Closing date is May 1st."},
        ]

        prompt = subject._build_system_prompt(property_info, rag_results)

        assert "Relevant Documents:" in prompt
        assert "The purchase agreement states a price of $300k." in prompt
        assert "Closing date is May 1st." in prompt
        assert "123 Main St" in prompt

    def test_build_system_prompt_omits_relevant_documents_section_when_no_rag_results(self, subject):
        property_info = PropertyInfo(id="prop-1", latitude=37.4, longitude=-122.0)

        prompt = subject._build_system_prompt(property_info, [])

        assert "Relevant Documents:" not in prompt

    @pytest.mark.parametrize(
        "property_kwargs,expected",
        [
            ({"formatted_address": "123 Main St"}, "Address: 123 Main St"),
            ({"city": "Sellersburg", "state": "IN"}, "Location: Sellersburg, IN"),
            ({"property_type": "Single Family"}, "Type: Single Family"),
            ({"bedrooms": 3}, "Bedrooms: 3"),
            ({"bathrooms": 2}, "Bathrooms: 2"),
            ({"square_footage": 1800}, "Square Footage: 1800"),
            ({"year_built": 1995}, "Year Built: 1995"),
            ({}, "No details available."),
        ],
    )
    def test_build_system_prompt_includes_property_fields(self, subject, property_kwargs, expected):
        property_info = PropertyInfo(id="prop-1", **property_kwargs)

        prompt = subject._build_system_prompt(property_info, [])

        assert expected in prompt

    @pytest.fixture
    def mock_chat_message_repository(self):
        yield AsyncMock(spec=ChatMessageRepository)

    @pytest.fixture
    def mock_property_repository(self):
        yield AsyncMock(spec=PropertyRepository)

    @pytest.fixture
    def mock_document_embedding_repository(self):
        yield AsyncMock(spec=DocumentEmbeddingRepository)

    @pytest.fixture
    def mock_openai_client(self):
        yield AsyncMock(spec=OpenAIClient)

    @pytest.fixture
    def subject(
        self,
        mock_chat_message_repository,
        mock_property_repository,
        mock_document_embedding_repository,
        mock_openai_client,
    ):
        yield ChatService(
            chat_message_repository=mock_chat_message_repository,
            property_repository=mock_property_repository,
            document_embedding_repository=mock_document_embedding_repository,
            openai_client=mock_openai_client,
            rag_top_k=3,
            max_tokens=500,
        )
