import random
from typing import Container
from unittest.mock import AsyncMock, MagicMock

from backend.models import PropertyFeatures, PropertyInfo
import pytest
from backend.exceptions import PropertyNotFoundError
from backend.services.property import PropertyService
from faker import Faker
from rentcast_client.api.default_api import DefaultApi
from rentcast_client.models import PropertyRecords200ResponseInner


def fake_property_record(
    no_features: bool = False,
):
    fake = Faker()

    features = None
    if not no_features:
        features = {
            "has_pool": fake.boolean(),
            "has_garage": fake.boolean(),
            "has_air_conditioning": fake.boolean(),
            "has_heating": fake.boolean(),
            "has_water_view": fake.boolean(),
        }

    return PropertyRecords200ResponseInner(
        formatted_address=fake.address(),
        city=fake.city(),
        state=fake.state_abbr(),
        zip_code=fake.zipcode(),
        latitude=fake.latitude(),
        longitude=fake.longitude(),
        property_type=random.choice(
            ["Single Family Home", "Apartment", "Condo", "Townhouse"]
        ),
        year_built=random.randint(1900, 2023),
        legal_description=fake.text(max_nb_chars=100),
        subdivision=fake.word(),
        zoning=random.choice(["Residential", "Commercial", "Industrial", "Mixed-Use"]),
        last_sale_date=fake.date_between(
            start_date="-5y", end_date="today"
        ).isoformat(),
        last_sale_price=random.randint(100000, 1000000),
        features=features,
    )


class AsyncMockWithValidateCall(AsyncMock):
    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)

    def __await__(self):
        return self().__await__()


class TestPropertyService:

    @pytest.mark.parametrize(
        "address, property_records",
        [
            (
                "123 Main St, Anytown, USA",
                [fake_property_record()],
            ),
            (
                "456 Elm St, Anytown, USA",
                [
                    fake_property_record(),
                    fake_property_record(),
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_search_property(
        self,
        subject: PropertyService,
        mock_client: AsyncMock,
        address: str,
        property_records: list[PropertyRecords200ResponseInner],
    ):
        mock_client.property_records.return_value = property_records

        actual = await subject.search_property(address)

        assert actual == PropertyInfo(
            id=property_records[0].id,
            formatted_address=property_records[0].formatted_address,
            address_line1=property_records[0].address_line1,
            address_line2=property_records[0].address_line2,
            city=property_records[0].city,
            state=property_records[0].state,
            zip_code=property_records[0].zip_code,
            county=property_records[0].county,
            latitude=property_records[0].latitude,
            longitude=property_records[0].longitude,
            property_type=property_records[0].property_type,
            bedrooms=property_records[0].bedrooms,
            bathrooms=property_records[0].bathrooms,
            square_footage=property_records[0].square_footage,
            lot_size=property_records[0].lot_size,
            year_built=property_records[0].year_built,
            assessor_id=property_records[0].assessor_id,
            legal_description=property_records[0].legal_description,
            subdivision=property_records[0].subdivision,
            zoning=property_records[0].zoning,
            last_sale_date=property_records[0].last_sale_date,
            last_sale_price=property_records[0].last_sale_price,
            features=PropertyFeatures(**property_records[0].features.model_dump()),
            owner_occupied=property_records[0].owner_occupied,
        )

    @pytest.mark.asyncio
    async def test_search_property_when_features_are_missing(
        self,
        subject: PropertyService,
        mock_client: AsyncMock,
    ):
        property_records = [fake_property_record(no_features=True)]
        mock_client.property_records.return_value = property_records
        actual = await subject.search_property("123 Main St, Anytown, USA")

        assert actual == PropertyInfo(
            id=property_records[0].id,
            formatted_address=property_records[0].formatted_address,
            address_line1=property_records[0].address_line1,
            address_line2=property_records[0].address_line2,
            city=property_records[0].city,
            state=property_records[0].state,
            zip_code=property_records[0].zip_code,
            county=property_records[0].county,
            latitude=property_records[0].latitude,
            longitude=property_records[0].longitude,
            property_type=property_records[0].property_type,
            bedrooms=property_records[0].bedrooms,
            bathrooms=property_records[0].bathrooms,
            square_footage=property_records[0].square_footage,
            lot_size=property_records[0].lot_size,
            year_built=property_records[0].year_built,
            assessor_id=property_records[0].assessor_id,
            legal_description=property_records[0].legal_description,
            subdivision=property_records[0].subdivision,
            zoning=property_records[0].zoning,
            last_sale_date=property_records[0].last_sale_date,
            last_sale_price=property_records[0].last_sale_price,
            features=None,
            owner_occupied=property_records[0].owner_occupied,
        )

    @pytest.mark.asyncio
    async def test_search_property_not_found(
        self, subject: PropertyService, mock_client: AsyncMock
    ):
        mock_client.property_records.return_value = []

        with pytest.raises(PropertyNotFoundError):
            await subject.search_property("123 Main St, Anytown, USA")

    @pytest.fixture
    def mock_client(self):
        mock = AsyncMock(spec=DefaultApi)
        mock.property_records = AsyncMockWithValidateCall()
        yield mock

    @pytest.fixture
    def subject(self, test_container: Container, mock_client: AsyncMock):
        with test_container.override_providers(rentcast_client=mock_client):
            yield test_container.property_service()
