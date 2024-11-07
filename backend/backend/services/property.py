import logging

from backend.models import PropertyFeatures, PropertyInfo
from backend.repositories.properties import PropertyRepository
from backend.services.document import DocumentService
from rentcast_client.api.default_api import DefaultApi
from backend.exceptions import DocumentNotFoundError, PropertyNotFoundError


class PropertyService:
    def __init__(
        self,
        client: DefaultApi,
        property_repository: PropertyRepository,
        document_service: DocumentService,
    ):
        self._client = client
        self._property_repository = property_repository
        self._document_service = document_service
        self._logger = logging.getLogger(self.__class__.__name__)

    async def search_property(self, address: str) -> PropertyInfo:
        """
        Get the property for the given address.

        Args:
            address (str): The address of the property to search for.

        Returns:
            PropertyInfo: The property details.

        Raises:
            PropertyNotFoundError: If no properties are found for the given address.

        Note:
            If multiple properties are found for the given address, a warning is logged and the first property is returned.
        """

        properties = await self._client.property_records(address)

        if not properties:
            raise PropertyNotFoundError

        if len(properties) > 1:
            self._logger.warning("Found multiple properties for address: %s", address)

        print(properties[0])

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
            features=(
                PropertyFeatures(**properties[0].features.model_dump())
                if properties[0].features
                else None
            ),
            owner_occupied=properties[0].owner_occupied,
        )

    async def create_property(
        self,
        property_data: PropertyInfo,
    ) -> PropertyInfo:
        """
        Create a new property.

        Args:
            property_data (PropertyInfo): The property data.
            images (List[UploadFile]): The images.
            supporting_docs (List[UploadFile]): The supporting documents.

        Returns:
            PropertyInfo: The created property.

        Raises:
            DocumentNotFoundError: If the document does not exist.
        """

        if not await self._document_service.exists(property_data.rentcast_id):
            raise DocumentNotFoundError

        return await self._property_repository.insert_property(property_data)
