import logging

from rentcast_client.api.default_rentcast import DefaultRentcast

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.clients.census_geocoder import CensusGeocoderClient
from backend.clients.tiger import TigerWebClient
from backend.exceptions import DocumentNotFoundError, DualAgencyNotAllowedError, PropertyNotFoundError
from backend.models import (
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


class PropertyService:
    def __init__(
        self,
        client: DefaultRentcast,
        property_repository: PropertyRepository,
        representation_repository: RepresentationRepository,
        document_repository: DocumentRepository,
        document_service: DocumentService,
        census_geocoder_client: CensusGeocoderClient,
        tiger_web_client: TigerWebClient,
        county_boundary_repository: CountyBoundaryRepository,
        arcgis_parcels_client: ArcGISParcelsClient,
        parcel_repository: ParcelRepository,
        arcgis_parcels_supported_states: set[str],
        brokerage_repository: BrokerageRepository,
    ):
        self._client = client
        self._property_repository = property_repository
        self._representation_repository = representation_repository
        self._document_repository = document_repository
        self._document_service = document_service
        self._census_geocoder_client = census_geocoder_client
        self._tiger_web_client = tiger_web_client
        self._county_boundary_repository = county_boundary_repository
        self._arcgis_parcels_client = arcgis_parcels_client
        self._parcel_repository = parcel_repository
        self._arcgis_parcels_supported_states = arcgis_parcels_supported_states
        self._brokerage_repository = brokerage_repository
        self._logger = logging.getLogger(self.__class__.__name__)

    async def search_property(self, address: str) -> Property:
        properties = await self._client.property_records(address)
        if not properties:
            raise PropertyNotFoundError
        p = properties[0]
        return Property(
            rentcast_id=p.id,
            address_line1=p.address_line1,
            address_line2=p.address_line2,
            city=p.city,
            state=p.state,
            zip_code=p.zip_code,
            latitude=p.latitude,
            longitude=p.longitude,
            property_type=p.property_type,
            bedrooms=p.bedrooms,
            bathrooms=p.bathrooms,
            square_footage=p.square_footage,
            lot_size=p.lot_size,
            year_built=p.year_built,
            last_sale_date=p.last_sale_date,
            last_sale_price=p.last_sale_price,
            owner_occupied=p.owner_occupied,
        )

    async def create_property(self, request: CreatePropertyRequest, brokerage_id: str) -> PropertyResponse:
        for doc in request.documents or []:
            if not await self._document_service.exists(doc.id):
                raise DocumentNotFoundError

        property_data = Property(
            rentcast_id=request.rentcast_id,
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
            county_fips=request.county_fips,
            latitude=request.latitude,
            longitude=request.longitude,
            property_type=request.property_type,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            square_footage=request.square_footage,
            lot_size=request.lot_size,
            year_built=request.year_built,
            last_sale_date=request.last_sale_date,
            last_sale_price=request.last_sale_price,
            owner_occupied=request.owner_occupied,
            architecture_type=request.architecture_type,
            cooling=request.cooling,
            cooling_type=request.cooling_type,
            exterior_type=request.exterior_type,
            floor_count=request.floor_count,
            foundation_type=request.foundation_type,
            garage=request.garage,
            garage_type=request.garage_type,
            heating=request.heating,
            heating_type=request.heating_type,
            pool=request.pool,
            roof_type=request.roof_type,
            room_count=request.room_count,
            unit_count=request.unit_count,
        )

        boundary = await self._enrich_with_county(property_data)
        saved_property = self._property_repository.insert(property_data)

        parcel = await self._enrich_with_parcel(
            property_id=saved_property.id,
            state=saved_property.state,
            latitude=saved_property.latitude,
            longitude=saved_property.longitude,
        )

        rep = Representation(
            property_id=saved_property.id,
            brokerage_id=brokerage_id,
            role=request.role,
        )
        saved_rep = self._representation_repository.insert(rep)

        if request.documents:
            docs = [Document(id=d.id, property_id=saved_property.id, filename=d.filename) for d in request.documents]
            self._document_repository.insert_many(docs)

        documents = self._document_repository.get_by_property_id(saved_property.id)
        return self._to_response(saved_property, saved_rep, boundary, parcel, documents)

    async def add_representation(self, property_id: str, role: str, brokerage_id: str) -> PropertyResponse:
        prop = self._property_repository.get(property_id)
        if prop is None:
            raise PropertyNotFoundError(f"Property {property_id} not found")

        opposite_count = self._representation_repository.count_opposite_role(property_id, brokerage_id, role)
        if opposite_count > 0:
            brokerage = self._brokerage_repository.get_by_id(brokerage_id)
            if brokerage is None or not brokerage.allow_dual_agency:
                raise DualAgencyNotAllowedError

        rep = Representation(
            property_id=property_id,
            brokerage_id=brokerage_id,
            role=role,
        )
        saved_rep = self._representation_repository.insert(rep)

        boundary = None
        if prop.county_fips:
            boundary = self._county_boundary_repository.get_by_fips(prop.county_fips)
        parcel = self._parcel_repository.get_by_property_id(property_id)
        documents = self._document_repository.get_by_property_id(property_id)
        return self._to_response(prop, saved_rep, boundary, parcel, documents)

    async def list_properties(self, brokerage_id: str) -> list[PropertyResponse]:
        pairs = self._representation_repository.list_with_property(brokerage_id)
        result = []
        for rep, prop in pairs:
            boundary = None
            if prop.county_fips:
                boundary = self._county_boundary_repository.get_by_fips(prop.county_fips)
            parcel = self._parcel_repository.get_by_property_id(prop.id)
            documents = self._document_repository.get_by_property_id(prop.id)
            result.append(self._to_response(prop, rep, boundary, parcel, documents))
        return result

    async def list_county_fips(self) -> list[str]:
        return self._property_repository.list_county_fips()

    async def append_document(self, property_id: str, document: DocumentInfo, brokerage_id: str) -> PropertyResponse:
        if not await self._document_service.exists(document.id):
            raise DocumentNotFoundError

        prop = self._property_repository.get(property_id)
        if prop is None:
            raise PropertyNotFoundError(f"Property {property_id} not found")

        pairs = self._representation_repository.list_with_property(brokerage_id)
        rep = next((r for r, p in pairs if p.id == property_id), None)
        if rep is None:
            raise PropertyNotFoundError(f"Property {property_id} not found for brokerage")

        self._document_repository.insert_many(
            [Document(id=document.id, property_id=property_id, filename=document.filename)]
        )

        boundary = self._county_boundary_repository.get_by_fips(prop.county_fips) if prop.county_fips else None
        parcel = self._parcel_repository.get_by_property_id(property_id)
        documents = self._document_repository.get_by_property_id(property_id)
        return self._to_response(prop, rep, boundary, parcel, documents)

    async def remove_document(self, property_id: str, doc_id: str, brokerage_id: str) -> PropertyResponse:
        prop = self._property_repository.get(property_id)
        if prop is None:
            raise PropertyNotFoundError(f"Property {property_id} not found")

        pairs = self._representation_repository.list_with_property(brokerage_id)
        rep = next((r for r, p in pairs if p.id == property_id), None)
        if rep is None:
            raise PropertyNotFoundError(f"Property {property_id} not found for brokerage")

        self._document_repository.delete(doc_id)
        await self._document_service.delete(doc_id)

        boundary = self._county_boundary_repository.get_by_fips(prop.county_fips) if prop.county_fips else None
        parcel = self._parcel_repository.get_by_property_id(property_id)
        documents = self._document_repository.get_by_property_id(property_id)
        return self._to_response(prop, rep, boundary, parcel, documents)

    async def _enrich_with_county(self, property_data: Property) -> CountyBoundary | None:
        if property_data.latitude is None or property_data.longitude is None:
            return None
        try:
            county_fips = await self._census_geocoder_client.get_county_fips(
                property_data.latitude, property_data.longitude
            )
        except Exception:
            self._logger.warning(
                "Failed to fetch county FIPS for lat=%s lon=%s",
                property_data.latitude,
                property_data.longitude,
            )
            return None

        property_data.county_fips = county_fips

        if county_fips is None:
            return None

        existing = self._county_boundary_repository.get_by_fips(county_fips)
        if existing:
            return existing

        try:
            polygon = await self._tiger_web_client.get_county_polygon(county_fips)
        except Exception:
            self._logger.warning("Failed to fetch county polygon for FIPS %s", county_fips)
            return None

        if polygon is None:
            return None

        boundary = CountyBoundary(fips=county_fips, geometry=polygon)
        return self._county_boundary_repository.upsert(boundary)

    async def _enrich_with_parcel(
        self,
        property_id: str,
        state: str | None,
        latitude: float | None,
        longitude: float | None,
    ) -> Parcel | None:
        if state not in self._arcgis_parcels_supported_states:
            return None
        if latitude is None or longitude is None:
            return None

        try:
            result = await self._arcgis_parcels_client.get_parcel(latitude, longitude)
        except Exception:
            self._logger.warning(
                "Failed to fetch parcel for lat=%s lon=%s",
                latitude,
                longitude,
            )
            return None

        if result is None:
            return None

        nguid = result["nguid"]
        parcel = Parcel(
            nguid=nguid,
            property_id=property_id,
            state_parcel_id=result.get("state_parcel_id"),
            geometry=result.get("geometry"),
        )
        return self._parcel_repository.upsert(parcel)

    def _to_response(
        self,
        property_data: Property,
        representation: Representation,
        boundary: CountyBoundary | None,
        parcel: Parcel | None,
        documents: list[Document],
    ) -> PropertyResponse:
        return PropertyResponse(
            **property_data.model_dump(),
            representation_id=representation.id,
            role=representation.role,
            county_polygon=boundary.geometry if boundary else None,
            parcel_polygon=parcel.geometry if parcel else None,
            documents=[DocumentInfo(id=d.id, filename=d.filename) for d in documents],
        )
