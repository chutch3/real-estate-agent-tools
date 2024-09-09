import logging
from backend.clients.rentcast import RentcastClient
from backend.exceptions import PropertyNotFoundError


class PropertyService:
    def __init__(self, client: RentcastClient):
        self._client = client
        self._logger = logging.getLogger(__name__)

    async def get_property(self, address: str):
        """
        Get the property for the given address.

        This method searches for a property using the provided address and returns the first matching result.

        Args:
            address (str): The address of the property to search for.

        Returns:
            dict: A dictionary containing the property details.

        Raises:
            PropertyNotFoundError: If no properties are found for the given address.

        Note:
            If multiple properties are found for the given address, a warning is logged and the first property is returned.
        """
        properties = await self._client.search_properties(address)
        if not properties:
            raise PropertyNotFoundError

        if len(properties) > 1:
            self._logger.warning("Found multiple properties for address: %s", address)

        return properties[0]
