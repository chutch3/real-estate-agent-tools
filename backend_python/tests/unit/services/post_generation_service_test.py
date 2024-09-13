from unittest.mock import AsyncMock, Mock
from backend.container import Container
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.services.document import DocumentService
from backend.services.post_generation import PostGenerationService
import pytest

from backend.clients.openai import OpenAIClient
from backend.template_loader import TemplateLoader


class TestPostGenerationService:
    @pytest.mark.asyncio
    async def test_generate_post(
        self,
        subject: PostGenerationService,
        mock_openai_client: AsyncMock,
        mock_template_loader: Mock,
        mock_document_repository: AsyncMock,
    ):
        mock_template_loader.render_user_prompt.return_value = "default template"
        mock_template_loader.render_system_prompt.return_value = "system prompt"
        mock_openai_client.create_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_document_repository.query_embeddings.return_value = [
            {"text": "MLS sheet chunk 1"},
            {"text": "MLS sheet chunk 2"},
        ]
        mock_openai_client.generate_completion.return_value = (
            "generated post using the default template"
        )

        actual = await subject.generate_post(
            property_info={
                "address": "123 Main St, Anytown, USA",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "features": {
                    "has_pool": True,
                    "has_garage": True,
                },
            },
            agent_info={
                "name": "John Doe",
                "company": "John Doe Real Estate",
                "contact": "john.doe@example.com",
            },
        )
        assert actual == "generated post using the default template"

        mock_openai_client.create_embeddings.assert_awaited_once_with(
            "default template"
        )
        mock_document_repository.query_embeddings.assert_awaited_once_with(
            [[0.1, 0.2, 0.3]], limit=5
        )
        mock_openai_client.generate_completion.assert_awaited_once_with(
            system_prompt="system prompt",
            user_prompt="default template\n\nAdditional information from MLS sheet:\nMLS sheet chunk 1\nMLS sheet chunk 2",
            max_tokens=200,
        )

    @pytest.mark.asyncio
    async def test_generate_post_with_custom_template(
        self,
        subject: PostGenerationService,
        mock_openai_client: AsyncMock,
        mock_template_loader: Mock,
        mock_document_repository: AsyncMock,
    ):
        mock_template_loader.render_system_prompt.return_value = "system prompt"
        mock_template_loader.render_user_prompt.return_value = "custom template"
        mock_openai_client.create_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_document_repository.query_embeddings.return_value = [
            {"text": "MLS sheet chunk 1"},
            {"text": "MLS sheet chunk 2"},
        ]
        mock_openai_client.generate_completion.return_value = (
            "generated post using the custom template"
        )

        actual = await subject.generate_post(
            property_info={
                "address": "123 Main St, Anytown, USA",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "features": {
                    "has_pool": True,
                    "has_garage": True,
                },
            },
            agent_info={
                "name": "John Doe",
                "company": "John Doe Real Estate",
                "contact": "john.doe@example.com",
            },
            custom_template="custom template",
        )
        assert actual == "generated post using the custom template"

        mock_openai_client.create_embeddings.assert_awaited_once_with("custom template")
        mock_document_repository.query_embeddings.assert_awaited_once_with(
            [[0.1, 0.2, 0.3]], limit=5
        )
        mock_openai_client.generate_completion.assert_awaited_once_with(
            system_prompt="system prompt",
            user_prompt="custom template\n\nAdditional information from MLS sheet:\nMLS sheet chunk 1\nMLS sheet chunk 2",
            max_tokens=200,
        )

    @pytest.fixture
    def mock_openai_client(self):
        return AsyncMock(spec=OpenAIClient)

    @pytest.fixture
    def mock_template_loader(self):
        return Mock(spec=TemplateLoader)

    @pytest.fixture
    def mock_document_repository(self):
        return AsyncMock(spec=DocumentEmbeddingRepository)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_openai_client: AsyncMock,
        mock_template_loader: Mock,
        mock_document_repository: AsyncMock,
    ):
        with test_container.override_providers(
            openai_client=mock_openai_client,
            template_loader=mock_template_loader,
            document_embedding_repository=mock_document_repository,
        ):
            yield test_container.post_generation_service()
