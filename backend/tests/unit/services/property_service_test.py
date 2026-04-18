from unittest.mock import AsyncMock, MagicMock

import pytest
from rentcast_client.api.default_rentcast import DefaultRentcast

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.clients.census_geocoder import CensusGeocoderClient
from backend.clients.tiger import TigerWebClient
from backend.exceptions import DocumentNotFoundError, DualAgencyNotAllowedError, PropertyNotFoundError
from backend.models import (
    Brokerage,
    CountyBoundary,
    CreatePropertyRequest,
    Document,
    DocumentInfo,
    Parcel,
    Property,
    PropertyResponse,
    Representation,
)
from backend.repositories.brokerage import BrokerageRepository
from backend.repositories.county_boundary import CountyBoundaryRepository
from backend.repositories.document import DocumentRepository
from backend.repositories.parcel import ParcelRepository
from backend.repositories.properties import PropertyRepository
from backend.repositories.representation import RepresentationRepository
from backend.services.document import DocumentService
from backend.services.property import PropertyService


class TestPropertyService:
    @pytest.mark.asyncio
    async def test_create_property_returns_response(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
    ):
        saved = Property(id="new-id", city="Jeffersonville", state="IN")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None
        saved_rep = Representation(id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent")
        mock_representation_repository.insert.return_value = saved_rep

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", city="Jeffersonville", state="IN"),
            brokerage_id="brok-1",
        )

        assert isinstance(result, PropertyResponse)
        assert result.id == "new-id"
        assert result.representation_id == "rep-id"
        assert result.role == "listing_agent"

    @pytest.mark.asyncio
    async def test_create_property_inserts_property_and_representation(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
    ):
        saved = Property(id="new-id")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None
        saved_rep = Representation(id="rep-id", property_id="new-id", brokerage_id="brok-1", role="buyers_agent")
        mock_representation_repository.insert.return_value = saved_rep

        await subject.create_property(
            CreatePropertyRequest(role="buyers_agent"),
            brokerage_id="brok-1",
        )

        mock_property_repository.insert.assert_called_once()
        inserted_rep = mock_representation_repository.insert.call_args[0][0]
        assert inserted_rep.role == "buyers_agent"
        assert inserted_rep.brokerage_id == "brok-1"
        assert inserted_rep.property_id == "new-id"

    @pytest.mark.asyncio
    async def test_create_property_enriches_with_county(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
    ):
        polygon = {"type": "Polygon", "coordinates": [[[0, 0]]]}
        saved = Property(id="new-id", county_fips="21111")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = "21111"
        mock_county_boundary_repository.get_by_fips.return_value = None
        mock_tiger_web_client.get_county_polygon.return_value = polygon
        mock_county_boundary_repository.upsert.return_value = CountyBoundary(fips="21111", geometry=polygon)
        mock_representation_repository.insert.return_value = Representation(
            id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent"
        )

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", latitude=38.2, longitude=-85.7),
            brokerage_id="brok-1",
        )

        mock_census_geocoder_client.get_county_fips.assert_awaited_once_with(38.2, -85.7)
        assert result.county_polygon == polygon

    @pytest.mark.asyncio
    async def test_create_property_enriches_with_parcel(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
        mock_arcgis_parcels_client: AsyncMock,
        mock_parcel_repository: MagicMock,
    ):
        polygon = {"type": "Polygon", "coordinates": [[[0, 0]]]}
        saved = Property(id="new-id", state="IN", latitude=39.77, longitude=-86.16)
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None
        mock_arcgis_parcels_client.get_parcel.return_value = {
            "nguid": "test-nguid",
            "state_parcel_id": "102403200259000013",
            "geometry": polygon,
        }
        stored_parcel = Parcel(nguid="test-nguid", property_id="new-id", geometry=polygon)
        mock_parcel_repository.upsert.return_value = stored_parcel
        mock_parcel_repository.get_by_property_id.return_value = stored_parcel
        mock_representation_repository.insert.return_value = Representation(
            id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent"
        )

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", state="IN", latitude=39.77, longitude=-86.16),
            brokerage_id="brok-1",
        )

        mock_arcgis_parcels_client.get_parcel.assert_awaited_once_with(39.77, -86.16)
        mock_parcel_repository.upsert.assert_called_once()
        upserted = mock_parcel_repository.upsert.call_args[0][0]
        assert upserted.state_parcel_id == "102403200259000013"
        assert result.parcel_polygon == polygon

    @pytest.mark.asyncio
    async def test_create_property_skips_parcel_for_unsupported_state(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
        mock_arcgis_parcels_client: AsyncMock,
    ):
        saved = Property(id="new-id", state="KY")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None
        mock_representation_repository.insert.return_value = Representation(
            id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent"
        )

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", state="KY", latitude=38.2, longitude=-85.7),
            brokerage_id="brok-1",
        )

        mock_arcgis_parcels_client.get_parcel.assert_not_awaited()
        assert result.parcel_polygon is None

    @pytest.mark.asyncio
    async def test_create_property_proceeds_when_census_geocoder_fails(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
    ):
        saved = Property(id="new-id")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.side_effect = Exception("network error")
        mock_representation_repository.insert.return_value = Representation(
            id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent"
        )

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", latitude=38.2, longitude=-85.7),
            brokerage_id="brok-1",
        )

        assert isinstance(result, PropertyResponse)
        assert result.county_polygon is None

    @pytest.mark.asyncio
    async def test_create_property_proceeds_when_parcel_client_raises(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_census_geocoder_client: AsyncMock,
        mock_arcgis_parcels_client: AsyncMock,
    ):
        saved = Property(id="new-id", state="IN")
        mock_property_repository.insert.return_value = saved
        mock_census_geocoder_client.get_county_fips.return_value = None
        mock_arcgis_parcels_client.get_parcel.side_effect = Exception("network error")
        mock_representation_repository.insert.return_value = Representation(
            id="rep-id", property_id="new-id", brokerage_id="brok-1", role="listing_agent"
        )

        result = await subject.create_property(
            CreatePropertyRequest(role="listing_agent", state="IN", latitude=39.77, longitude=-86.16),
            brokerage_id="brok-1",
        )

        assert result.parcel_polygon is None

    @pytest.mark.asyncio
    async def test_add_representation_raises_when_dual_agency_disallowed(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_brokerage_repository: MagicMock,
    ):
        mock_property_repository.get.return_value = Property(id="prop-1")
        mock_representation_repository.count_opposite_role.return_value = 1
        mock_brokerage_repository.get_by_id.return_value = Brokerage(
            id="brok-1", name="No Dual Agency", allow_dual_agency=False
        )

        with pytest.raises(DualAgencyNotAllowedError):
            await subject.add_representation("prop-1", "buyers_agent", "brok-1")

    @pytest.mark.asyncio
    async def test_add_representation_succeeds_when_brokerage_allows_dual_agency(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_brokerage_repository: MagicMock,
    ):
        mock_property_repository.get.return_value = Property(id="prop-1")
        mock_representation_repository.count_opposite_role.return_value = 1
        mock_brokerage_repository.get_by_id.return_value = Brokerage(
            id="brok-1", name="Dual Agency OK", allow_dual_agency=True
        )
        saved_rep = Representation(id="rep-2", property_id="prop-1", brokerage_id="brok-1", role="buyers_agent")
        mock_representation_repository.insert.return_value = saved_rep

        result = await subject.add_representation("prop-1", "buyers_agent", "brok-1")

        assert isinstance(result, PropertyResponse)
        assert result.role == "buyers_agent"

    @pytest.mark.asyncio
    async def test_add_representation_raises_when_property_not_found(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
    ):
        mock_property_repository.get.return_value = None

        with pytest.raises(PropertyNotFoundError):
            await subject.add_representation("nonexistent", "listing_agent", "brok-1")

    @pytest.mark.asyncio
    async def test_list_properties_returns_responses(
        self,
        subject: PropertyService,
        mock_representation_repository: MagicMock,
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brok-1", role="listing_agent")
        prop = Property(id="prop-1", city="Louisville")
        mock_representation_repository.list_with_property.return_value = [(rep, prop)]

        result = await subject.list_properties("brok-1")

        assert len(result) == 1
        assert isinstance(result[0], PropertyResponse)
        assert result[0].representation_id == "rep-1"
        assert result[0].role == "listing_agent"

    @pytest.mark.asyncio
    async def test_list_county_fips_delegates_to_repository(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
    ):
        mock_property_repository.list_county_fips.return_value = ["21111", "18019"]

        result = await subject.list_county_fips()

        mock_property_repository.list_county_fips.assert_called_once()
        assert result == ["21111", "18019"]

    @pytest.mark.asyncio
    async def test_append_document_returns_response_with_document(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_document_repository: MagicMock,
        mock_document_service: AsyncMock,
    ):
        prop = Property(id="prop-1")
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brok-1", role="listing_agent")
        doc = Document(id="doc-1", property_id="prop-1", filename="contract.pdf")
        mock_document_service.exists.return_value = True
        mock_property_repository.get.return_value = prop
        mock_representation_repository.list_with_property.return_value = [(rep, prop)]
        mock_document_repository.get_by_property_id.return_value = [doc]

        result = await subject.append_document("prop-1", DocumentInfo(id="doc-1", filename="contract.pdf"), "brok-1")

        mock_document_repository.insert_many.assert_called_once()
        inserted = mock_document_repository.insert_many.call_args[0][0]
        assert inserted[0].id == "doc-1"
        assert inserted[0].property_id == "prop-1"
        assert isinstance(result, PropertyResponse)
        assert any(d.id == "doc-1" for d in result.documents)

    @pytest.mark.asyncio
    async def test_append_document_raises_when_document_not_in_storage(
        self,
        subject: PropertyService,
        mock_document_service: AsyncMock,
    ):
        mock_document_service.exists.return_value = False

        with pytest.raises(DocumentNotFoundError):
            await subject.append_document("prop-1", DocumentInfo(id="doc-1", filename="contract.pdf"), "brok-1")

    @pytest.mark.asyncio
    async def test_append_document_raises_when_property_not_found(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_document_service: AsyncMock,
    ):
        mock_document_service.exists.return_value = True
        mock_property_repository.get.return_value = None

        with pytest.raises(PropertyNotFoundError):
            await subject.append_document("prop-1", DocumentInfo(id="doc-1", filename="contract.pdf"), "brok-1")

    @pytest.mark.asyncio
    async def test_append_document_raises_when_property_not_in_brokerage(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_document_service: AsyncMock,
    ):
        mock_document_service.exists.return_value = True
        mock_property_repository.get.return_value = Property(id="prop-1")
        mock_representation_repository.list_with_property.return_value = []

        with pytest.raises(PropertyNotFoundError):
            await subject.append_document("prop-1", DocumentInfo(id="doc-1", filename="contract.pdf"), "brok-1")

    @pytest.mark.asyncio
    async def test_remove_document_deletes_from_repo_and_storage(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_document_repository: MagicMock,
        mock_document_service: AsyncMock,
    ):
        prop = Property(id="prop-1")
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brok-1", role="listing_agent")
        mock_property_repository.get.return_value = prop
        mock_representation_repository.list_with_property.return_value = [(rep, prop)]
        mock_document_repository.get_by_property_id.return_value = []

        result = await subject.remove_document("prop-1", "doc-1", "brok-1")

        mock_document_repository.delete.assert_called_once_with("doc-1")
        mock_document_service.delete.assert_awaited_once_with("doc-1")
        assert isinstance(result, PropertyResponse)

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_property_not_found(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
    ):
        mock_property_repository.get.return_value = None

        with pytest.raises(PropertyNotFoundError):
            await subject.remove_document("prop-1", "doc-1", "brok-1")

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_property_not_in_brokerage(
        self,
        subject: PropertyService,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
    ):
        mock_property_repository.get.return_value = Property(id="prop-1")
        mock_representation_repository.list_with_property.return_value = []

        with pytest.raises(PropertyNotFoundError):
            await subject.remove_document("prop-1", "doc-1", "brok-1")

    @pytest.fixture
    def mock_client(self):
        return AsyncMock(spec=DefaultRentcast)

    @pytest.fixture
    def mock_property_repository(self):
        mock = MagicMock(spec=PropertyRepository)
        mock.insert.return_value = Property(id="prop-id")
        return mock

    @pytest.fixture
    def mock_representation_repository(self):
        mock = MagicMock(spec=RepresentationRepository)
        mock.count_opposite_role.return_value = 0
        mock.insert.return_value = Representation(
            id="rep-id", property_id="prop-id", brokerage_id="brok-1", role="listing_agent"
        )
        mock.list_with_property.return_value = []
        return mock

    @pytest.fixture
    def mock_document_repository(self):
        mock = MagicMock(spec=DocumentRepository)
        mock.get_by_property_id.return_value = []
        return mock

    @pytest.fixture
    def mock_document_service(self):
        mock = AsyncMock(spec=DocumentService)
        mock.exists.return_value = True
        return mock

    @pytest.fixture
    def mock_census_geocoder_client(self):
        mock = AsyncMock(spec=CensusGeocoderClient)
        mock.get_county_fips.return_value = None
        return mock

    @pytest.fixture
    def mock_tiger_web_client(self):
        return AsyncMock(spec=TigerWebClient)

    @pytest.fixture
    def mock_county_boundary_repository(self):
        mock = MagicMock(spec=CountyBoundaryRepository)
        mock.get_by_fips.return_value = None
        return mock

    @pytest.fixture
    def mock_arcgis_parcels_client(self):
        mock = AsyncMock(spec=ArcGISParcelsClient)
        mock.get_parcel.return_value = None
        return mock

    @pytest.fixture
    def mock_parcel_repository(self):
        mock = MagicMock(spec=ParcelRepository)
        mock.get_by_property_id.return_value = None
        mock.upsert.return_value = None
        return mock

    @pytest.fixture
    def mock_brokerage_repository(self):
        mock = MagicMock(spec=BrokerageRepository)
        mock.get_by_id.return_value = Brokerage(id="brok-1", name="Test", allow_dual_agency=False)
        return mock

    @pytest.fixture
    def subject(
        self,
        test_container,
        mock_client: AsyncMock,
        mock_property_repository: MagicMock,
        mock_representation_repository: MagicMock,
        mock_document_repository: MagicMock,
        mock_document_service: AsyncMock,
        mock_census_geocoder_client: AsyncMock,
        mock_tiger_web_client: AsyncMock,
        mock_county_boundary_repository: MagicMock,
        mock_arcgis_parcels_client: AsyncMock,
        mock_parcel_repository: MagicMock,
        mock_brokerage_repository: MagicMock,
    ):
        with test_container.override_providers(
            rentcast_client=mock_client,
            property_repository=mock_property_repository,
            representation_repository=mock_representation_repository,
            document_repository=mock_document_repository,
            document_service=mock_document_service,
            census_geocoder_client=mock_census_geocoder_client,
            tiger_web_client=mock_tiger_web_client,
            county_boundary_repository=mock_county_boundary_repository,
            arcgis_parcels_client=mock_arcgis_parcels_client,
            parcel_repository=mock_parcel_repository,
            arcgis_parcels_supported_states={"IN"},
            brokerage_repository=mock_brokerage_repository,
        ):
            yield test_container.property_service()
