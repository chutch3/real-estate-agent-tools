from unittest.mock import AsyncMock

from backend.clients.rentcast import RentcastClient
from backend.exceptions import PropertyNotFoundError
import pytest
from backend.services.property import PropertyService


class TestPropertyService:

    @pytest.mark.parametrize(
        "address, search_properties_return_value",
        [
            (
                "123 Main St, Anytown, USA",
                [
                    {
                        "address": "123 Main St, Anytown, USA",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345",
                    }
                ],
            ),
            (
                "456 Elm St, Anytown, USA",
                [
                    {
                        "address": "456 Elm St, Anytown, USA",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345",
                    },
                    {
                        "address": "456 Elm St, Anytown, USA",
                        "city": "Anytown",
                        "state": "CA",
                        "zip_code": "12345",
                    },
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_property(
        self,
        subject: PropertyService,
        mock_client: AsyncMock,
        address,
        search_properties_return_value,
    ):
        mock_client.search_properties.return_value = search_properties_return_value

        actual = await subject.get_property(address)

        assert actual == search_properties_return_value[0]

    @pytest.mark.asyncio
    async def test_get_property_not_found(
        self, subject: PropertyService, mock_client: AsyncMock
    ):
        mock_client.search_properties.return_value = []

        with pytest.raises(PropertyNotFoundError):
            await subject.get_property("123 Main St, Anytown, USA")

    @pytest.fixture
    def mock_client(self):
        yield AsyncMock(spec=RentcastClient)

    @pytest.fixture
    def subject(self, test_container, mock_client: AsyncMock):
        with test_container.override_providers(rentcast_client=mock_client):
            yield test_container.property_service()
