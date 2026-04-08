import logging

from rentcast_client.api.default_rentcast import DefaultRentcast

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.clients.census_geocoder import CensusGeocoderClient
from backend.clients.tiger import TigerWebClient
from backend.exceptions import DocumentNotFoundError, PropertyNotFoundError
from backend.models import (
    CountyBoundary,
    DocumentInfo,
    ParcelBoundary,
    PropertyFeatures,
    PropertyInfo,
    PropertyResponse,
)
from backend.repositories.county_boundary import CountyBoundaryRepository
from backend.repositories.parcel_boundary import ParcelBoundaryRepository
from backend.repositories.properties import PropertyRepository
from backend.services.document import DocumentService


class PropertyService:
    def __init__(
        self,
        client: DefaultRentcast,
        property_repository: PropertyRepository,
        document_service: DocumentService,
        census_geocoder_client: CensusGeocoderClient,
        tiger_web_client: TigerWebClient,
        county_boundary_repository: CountyBoundaryRepository,
        arcgis_parcels_client: ArcGISParcelsClient,
        parcel_boundary_repository: ParcelBoundaryRepository,
        arcgis_parcels_supported_states: set[str],
    ):
        self._client = client
        self._property_repository = property_repository
        self._document_service = document_service
        self._census_geocoder_client = census_geocoder_client
        self._tiger_web_client = tiger_web_client
        self._county_boundary_repository = county_boundary_repository
        self._arcgis_parcels_client = arcgis_parcels_client
        self._parcel_boundary_repository = parcel_boundary_repository
        self._arcgis_parcels_supported_states = arcgis_parcels_supported_states
        self._logger = logging.getLogger(self.__class__.__name__)

    async def search_property(self, address: str) -> PropertyInfo:
        properties = await self._client.property_records(address)

        if not properties:
            raise PropertyNotFoundError

        if len(properties) > 1:
            self._logger.warning("Found multiple properties for address: %s", address)

        return PropertyInfo(
            rentcast_id=properties[0].id,
            formatted_address=properties[0].formatted_address,
            address_line1=properties[0].address_line1,
            address_line2=properties[0].address_line2,
            city=properties[0].city,
            state=properties[0].state,
            zip_code=properties[0].zip_code,
            county=properties[0].county,
            latitude=properties[0].latitude,
            longitude=properties[0].longitude,
            property_type=properties[0].property_type,
            bedrooms=properties[0].bedrooms,
            bathrooms=properties[0].bathrooms,
            square_footage=properties[0].square_footage,
            lot_size=properties[0].lot_size,
            year_built=properties[0].year_built,
            assessor_id=properties[0].assessor_id,
            legal_description=properties[0].legal_description,
            subdivision=properties[0].subdivision,
            zoning=properties[0].zoning,
            last_sale_date=properties[0].last_sale_date,
            last_sale_price=properties[0].last_sale_price,
            features=(PropertyFeatures(**properties[0].features.model_dump()) if properties[0].features else None),
            owner_occupied=properties[0].owner_occupied,
        )

    async def list_properties(self, brokerage_id: str) -> list[PropertyResponse]:
        properties = await self._property_repository.list_properties(brokerage_id)
        result = []
        for prop in properties:
            boundary = None
            if prop.county_fips:
                boundary = self._county_boundary_repository.get_by_fips(prop.county_fips)
            parcel = None
            if prop.parcel_nguid:
                parcel = self._parcel_boundary_repository.get_by_nguid(prop.parcel_nguid)
            result.append(self._to_response(prop, boundary, parcel))
        return result

    async def list_county_fips(self) -> list[str]:
        return await self._property_repository.list_county_fips()

    async def _enrich_with_county(self, property_data: PropertyInfo) -> CountyBoundary | None:
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

    async def _enrich_with_parcel(self, property_data: PropertyInfo) -> ParcelBoundary | None:
        if property_data.state not in self._arcgis_parcels_supported_states:
            return None

        try:
            result = await self._arcgis_parcels_client.get_parcel(property_data.latitude, property_data.longitude)
        except Exception:
            self._logger.warning(
                "Failed to fetch parcel for lat=%s lon=%s",
                property_data.latitude,
                property_data.longitude,
            )
            return None

        if result is None:
            return None

        nguid = result["nguid"]
        property_data.parcel_nguid = nguid

        existing = self._parcel_boundary_repository.get_by_nguid(nguid)
        if existing:
            return existing

        return self._parcel_boundary_repository.upsert(ParcelBoundary(nguid=nguid, geometry=result["geometry"]))

    async def create_property(self, property_data: PropertyInfo, brokerage_id: str) -> PropertyResponse:
        for doc in property_data.documents or []:
            doc_id = doc["id"] if isinstance(doc, dict) else doc.id
            if not await self._document_service.exists(doc_id):
                raise DocumentNotFoundError

        property_data.brokerage_id = brokerage_id

        boundary = await self._enrich_with_county(property_data)
        parcel = await self._enrich_with_parcel(property_data)
        saved = await self._property_repository.insert_property(property_data)
        return self._to_response(saved, boundary, parcel)

    async def append_document(self, property_id: str, document: DocumentInfo, brokerage_id: str) -> PropertyResponse:
        if not await self._document_service.exists(document.id):
            raise DocumentNotFoundError
        prop = await self._property_repository.append_document(property_id, document, brokerage_id)
        boundary = None
        if prop.county_fips:
            boundary = self._county_boundary_repository.get_by_fips(prop.county_fips)
        parcel = None
        if prop.parcel_nguid:
            parcel = self._parcel_boundary_repository.get_by_nguid(prop.parcel_nguid)
        return self._to_response(prop, boundary, parcel)

    async def remove_document(self, property_id: str, doc_id: str, brokerage_id: str) -> PropertyResponse:
        prop = await self._property_repository.remove_document(property_id, doc_id, brokerage_id)
        await self._document_service.delete(doc_id)
        boundary = None
        if prop.county_fips:
            boundary = self._county_boundary_repository.get_by_fips(prop.county_fips)
        parcel = None
        if prop.parcel_nguid:
            parcel = self._parcel_boundary_repository.get_by_nguid(prop.parcel_nguid)
        return self._to_response(prop, boundary, parcel)

    def _to_response(
        self,
        property_info: PropertyInfo,
        boundary: CountyBoundary | None,
        parcel: ParcelBoundary | None,
    ) -> PropertyResponse:
        return PropertyResponse(
            **property_info.model_dump(),
            county_polygon=boundary.geometry if boundary else None,
            parcel_polygon=parcel.geometry if parcel else None,
        )
