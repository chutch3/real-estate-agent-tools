import random
from typing import Container
from unittest.mock import AsyncMock, MagicMock

import pytest
from faker import Faker
from unittest.mock import AsyncMock, MagicMock

from backend.clients.census_geocoder import CensusGeocoderClient
from backend.clients.tiger import TigerWebClient
from backend.exceptions import DocumentNotFoundError, PropertyNotFoundError
from backend.models import CountyBoundary, DocumentInfo, PropertyFeatures, PropertyInfo, PropertyResponse
from backend.repositories.county_boundary import CountyBoundaryRepository
from backend.repositories.properties import PropertyRepository
from backend.services.document import DocumentService
from backend.services.property import PropertyService
from rentcast_client.api.default_rentcast import DefaultRentcast
from rentcast_client.models import RentcastPropertyRecords200ResponseInner
from tests.factories import PropertyInfoFactory
from typing import Container


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

    return RentcastPropertyRecords200ResponseInner(
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
        property_records: list[RentcastPropertyRecords200ResponseInner],
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
    async def test_create_property(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        property_data = PropertyInfo(
            rentcast_id="rentcast-123",
            latitude=37.4,
            longitude=-122.1,
            documents=[
                DocumentInfo(id="doc-uuid-1", filename="listing.pdf"),
                DocumentInfo(id="doc-uuid-2", filename="disclosure.pdf"),
            ],
        )
        saved = property_data.model_copy(update={"id": "new-id"})
        mock_property_repository.insert_property.return_value = saved
        mock_document_service.exists.return_value = True
        mock_census_geocoder_client.get_county_fips.return_value = None

        actual = await subject.create_property(property_data)

        mock_document_service.exists.assert_any_call("doc-uuid-1")
        mock_document_service.exists.assert_any_call("doc-uuid-2")
        mock_property_repository.insert_property.assert_called_once()
        assert isinstance(actual, PropertyResponse)
        assert actual.id == "new-id"

    @pytest.mark.asyncio
    async def test_create_property_enriches_with_county_polygon(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        polygon = {"type": "Polygon", "coordinates": [[[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 37.997]]]}
        property_data = PropertyInfo(rentcast_id="rentcast-123", latitude=38.2, longitude=-85.7)
        saved = property_data.model_copy(update={"id": "new-id", "county_fips": "21111"})
        mock_property_repository.insert_property.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = "21111"
        mock_county_boundary_repository.get_by_fips.return_value = None
        mock_tiger_web_client.get_county_polygon.return_value = polygon
        stored_boundary = CountyBoundary(fips="21111", geometry=polygon)
        mock_county_boundary_repository.upsert.return_value = stored_boundary

        actual = await subject.create_property(property_data)

        mock_census_geocoder_client.get_county_fips.assert_awaited_once_with(38.2, -85.7)
        mock_county_boundary_repository.get_by_fips.assert_called_once_with("21111")
        mock_tiger_web_client.get_county_polygon.assert_awaited_once_with("21111")
        mock_county_boundary_repository.upsert.assert_called_once()
        inserted = mock_property_repository.insert_property.call_args[0][0]
        assert inserted.county_fips == "21111"
        assert isinstance(actual, PropertyResponse)
        assert actual.county_polygon == polygon

    @pytest.mark.asyncio
    async def test_create_property_reuses_existing_county_boundary(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        polygon = {"type": "Polygon", "coordinates": [[[-86.035, 37.997], [-85.404, 38.375], [-86.035, 37.997]]]}
        existing_boundary = CountyBoundary(fips="21111", geometry=polygon)
        property_data = PropertyInfo(rentcast_id="rentcast-123", latitude=38.2, longitude=-85.7)
        saved = property_data.model_copy(update={"id": "new-id", "county_fips": "21111"})
        mock_property_repository.insert_property.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = "21111"
        mock_county_boundary_repository.get_by_fips.return_value = existing_boundary

        actual = await subject.create_property(property_data)

        mock_tiger_web_client.get_county_polygon.assert_not_awaited()
        mock_county_boundary_repository.upsert.assert_not_called()
        assert isinstance(actual, PropertyResponse)
        assert actual.county_polygon == polygon

    @pytest.mark.asyncio
    async def test_create_property_proceeds_when_census_geocoder_fails(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        property_data = PropertyInfo(rentcast_id="rentcast-123", latitude=38.2, longitude=-85.7)
        saved = property_data.model_copy(update={"id": "new-id"})
        mock_property_repository.insert_property.return_value = saved
        mock_census_geocoder_client.get_county_fips.side_effect = Exception("network error")

        actual = await subject.create_property(property_data)

        mock_tiger_web_client.get_county_polygon.assert_not_awaited()
        mock_county_boundary_repository.upsert.assert_not_called()
        inserted = mock_property_repository.insert_property.call_args[0][0]
        assert inserted.county_fips is None
        assert isinstance(actual, PropertyResponse)
        assert actual.county_polygon is None

    @pytest.mark.asyncio
    async def test_create_property_proceeds_when_tiger_web_fails(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        property_data = PropertyInfo(rentcast_id="rentcast-123", latitude=38.2, longitude=-85.7)
        saved = property_data.model_copy(update={"id": "new-id", "county_fips": "21111"})
        mock_property_repository.insert_property.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = "21111"
        mock_county_boundary_repository.get_by_fips.return_value = None
        mock_tiger_web_client.get_county_polygon.side_effect = Exception("network error")

        actual = await subject.create_property(property_data)

        inserted = mock_property_repository.insert_property.call_args[0][0]
        assert inserted.county_fips == "21111"
        assert isinstance(actual, PropertyResponse)
        assert actual.county_polygon is None

    @pytest.mark.asyncio
    async def test_create_property_without_documents(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        property_data = PropertyInfo(rentcast_id="rentcast-123", latitude=37.4, longitude=-122.1, documents=None)
        saved = property_data.model_copy(update={"id": "new-id"})
        mock_property_repository.insert_property.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None

        actual = await subject.create_property(property_data)

        mock_document_service.exists.assert_not_called()
        mock_property_repository.insert_property.assert_called_once()
        assert isinstance(actual, PropertyResponse)

    @pytest.mark.asyncio
    async def test_create_property_when_document_does_not_exist(
        self,
        subject: PropertyService,
        mock_document_service: AsyncMock,
    ):
        mock_document_service.exists.return_value = False
        property_data = PropertyInfo(
            rentcast_id="rentcast-123",
            latitude=37.4,
            longitude=-122.1,
            documents=[DocumentInfo(id="doc-uuid-missing", filename="missing.pdf")],
        )
        with pytest.raises(DocumentNotFoundError):
            await subject.create_property(property_data)

    @pytest.mark.asyncio
    async def test_append_document(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        doc = DocumentInfo(id="doc-1", filename="new.pdf")
        prop = PropertyInfo(rentcast_id="r", latitude=0, longitude=0, documents=[doc])
        mock_document_service.exists.return_value = True
        mock_property_repository.append_document.return_value = prop
        mock_county_boundary_repository.get_by_fips.return_value = None

        result = await subject.append_document("prop-id", doc)

        mock_document_service.exists.assert_called_once_with("doc-1")
        mock_property_repository.append_document.assert_called_once_with("prop-id", doc)
        assert isinstance(result, PropertyResponse)
        assert result.documents == [doc]

    @pytest.mark.asyncio
    async def test_append_document_when_document_does_not_exist(
        self,
        subject: PropertyService,
        mock_document_service: AsyncMock,
    ):
        mock_document_service.exists.return_value = False
        doc = DocumentInfo(id="missing", filename="missing.pdf")
        with pytest.raises(DocumentNotFoundError):
            await subject.append_document("prop-id", doc)

    @pytest.mark.asyncio
    async def test_remove_document(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        prop = PropertyInfo(rentcast_id="r", latitude=0, longitude=0, documents=[])
        mock_property_repository.remove_document.return_value = prop
        mock_county_boundary_repository.get_by_fips.return_value = None

        result = await subject.remove_document("prop-id", "doc-1")

        mock_property_repository.remove_document.assert_awaited_once_with("prop-id", "doc-1")
        mock_document_service.delete.assert_awaited_once_with("doc-1")
        assert isinstance(result, PropertyResponse)
        assert result.documents == []

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_doc_not_in_property(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
    ):
        mock_property_repository.remove_document.side_effect = DocumentNotFoundError()

        with pytest.raises(DocumentNotFoundError):
            await subject.remove_document("prop-id", "missing-doc")

        mock_document_service.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_list_properties(
        self,
        subject: PropertyService,
        property_info_factory: PropertyInfoFactory,
        mock_property_repository: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        props = [property_info_factory.build(county_fips=None), property_info_factory.build(county_fips=None)]
        mock_property_repository.list_properties.return_value = props

        actual = await subject.list_properties()

        mock_property_repository.list_properties.assert_called_once()
        assert len(actual) == 2
        assert all(isinstance(r, PropertyResponse) for r in actual)

    @pytest.mark.asyncio
    async def test_search_property_not_found(
        self, subject: PropertyService, mock_client: AsyncMock
    ):
        mock_client.property_records.return_value = []

        with pytest.raises(PropertyNotFoundError):
            await subject.search_property("123 Main St, Anytown, USA")

    @pytest.mark.asyncio
    async def test_list_county_fips(
        self,
        subject: PropertyService,
        mock_property_repository: AsyncMock,
    ):
        mock_property_repository.list_county_fips.return_value = ["21111", "18019"]

        actual = await subject.list_county_fips()

        mock_property_repository.list_county_fips.assert_awaited_once()
        assert actual == ["21111", "18019"]

    @pytest.fixture
    def mock_client(self):
        mock = AsyncMock(spec=DefaultRentcast)
        mock.property_records = AsyncMockWithValidateCall()
        yield mock

    @pytest.fixture
    def mock_property_repository(self):
        mock = AsyncMock(spec=PropertyRepository)
        yield mock

    @pytest.fixture
    def mock_document_service(self):
        mock = AsyncMock(spec=DocumentService)
        yield mock

    @pytest.fixture
    def mock_census_geocoder_client(self):
        yield AsyncMock(spec=CensusGeocoderClient)

    @pytest.fixture
    def mock_tiger_web_client(self):
        yield AsyncMock(spec=TigerWebClient)

    @pytest.fixture
    def mock_county_boundary_repository(self):
        yield MagicMock(spec=CountyBoundaryRepository)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_client: AsyncMock,
        mock_property_repository: AsyncMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        with test_container.override_providers(
            rentcast_client=mock_client,
            property_repository=mock_property_repository,
            document_service=mock_document_service,
            census_geocoder_client=mock_census_geocoder_client,
            tiger_web_client=mock_tiger_web_client,
            county_boundary_repository=mock_county_boundary_repository,
        ):
            yield test_container.property_service()
