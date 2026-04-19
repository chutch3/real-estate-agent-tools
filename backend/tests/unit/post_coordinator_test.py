from unittest.mock import AsyncMock

import pytest

from backend.exceptions import PropertyNotFoundError
from backend.models import DocumentInfo, PropertyResponse
from backend.post_coordinator import PostCoordinator
from backend.services import PostGenerationService, PropertyService


class TestPostCoordinator:
    @pytest.mark.asyncio
    async def test_generate_post_uses_property_id_and_brokerage_id(
        self,
        subject: PostCoordinator,
        mock_property_service: AsyncMock,
        mock_post_generation_service: AsyncMock,
    ):
        prop = PropertyResponse(
            id="prop-1",
            representation_id="rep-1",
            role="listing_agent",
            documents=[DocumentInfo(id="doc-1", filename="mls.pdf", consumer_visible=False)],
        )
        mock_property_service.get_property.return_value = prop
        mock_post_generation_service.generate_post.return_value = "generated post"

        result = await subject.generate_post(
            property_id="prop-1",
            brokerage_id="brok-1",
            agent_info={"name": "John Doe"},
        )

        assert result == "generated post"
        mock_property_service.get_property.assert_awaited_once_with("prop-1", "brok-1")

    @pytest.mark.asyncio
    async def test_generate_post_passes_doc_ids_to_generation_service(
        self,
        subject: PostCoordinator,
        mock_property_service: AsyncMock,
        mock_post_generation_service: AsyncMock,
    ):
        prop = PropertyResponse(
            id="prop-1",
            representation_id="rep-1",
            role="listing_agent",
            documents=[
                DocumentInfo(id="doc-1", filename="mls.pdf", consumer_visible=False),
                DocumentInfo(id="doc-2", filename="disclosures.pdf", consumer_visible=False),
            ],
        )
        mock_property_service.get_property.return_value = prop
        mock_post_generation_service.generate_post.return_value = "post"

        await subject.generate_post(
            property_id="prop-1",
            brokerage_id="brok-1",
            agent_info={"name": "John Doe"},
        )

        mock_post_generation_service.generate_post.assert_awaited_once_with(
            prop.model_dump(), {"name": "John Doe"}, None, doc_ids=["doc-1", "doc-2"]
        )

    @pytest.mark.asyncio
    async def test_generate_post_raises_when_property_not_found(
        self,
        subject: PostCoordinator,
        mock_property_service: AsyncMock,
    ):
        mock_property_service.get_property.side_effect = PropertyNotFoundError()

        with pytest.raises(PropertyNotFoundError):
            await subject.generate_post(
                property_id="missing",
                brokerage_id="brok-1",
                agent_info={"name": "John Doe"},
            )

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def mock_post_generation_service(self):
        yield AsyncMock(spec=PostGenerationService)

    @pytest.fixture
    def subject(self, test_container, mock_property_service, mock_post_generation_service):
        with test_container.override_providers(
            property_service=mock_property_service,
            post_generation_service=mock_post_generation_service,
        ):
            yield test_container.post_coordinator()
