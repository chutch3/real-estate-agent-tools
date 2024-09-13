from unittest.mock import AsyncMock

import pytest
from backend.post_coordinator import PostCoordinator
from backend.services import PostGenerationService, PropertyService


class TestPostCoordinator:

    @pytest.mark.parametrize(
        "address, agent_info, custom_template, expected",
        [
            (
                "123 Main St, Anytown, USA",
                {"name": "John Doe", "email": "john.doe@example.com"},
                "This is a test post",
                "This is a test post",
            ),
            (
                "456 Elm St, Anytown, USA",
                {"name": "Jane Doe", "email": "jane.doe@example.com"},
                None,
                "This is another test post",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_generate_post(
        self,
        subject: PostCoordinator,
        mock_property_service: AsyncMock,
        mock_post_generation_service: AsyncMock,
        address,
        agent_info,
        custom_template,
        expected,
    ):
        resolved_property = {
            "formatted_address": "123 Main St, Anytown, USA",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
        }

        mock_property_service.get_property.return_value = resolved_property
        mock_post_generation_service.generate_post.return_value = expected

        actual = await subject.generate_post(
            address,
            agent_info,
            custom_template,
        )

        assert actual == expected

        mock_post_generation_service.generate_post.assert_called_once_with(
            resolved_property, agent_info, custom_template
        )

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def mock_post_generation_service(self):
        yield AsyncMock(spec=PostGenerationService)

    @pytest.fixture
    def subject(
        self, test_container, mock_property_service, mock_post_generation_service
    ):
        with test_container.override_providers(
            property_service=mock_property_service,
            post_generation_service=mock_post_generation_service,
        ):
            yield test_container.post_coordinator()
