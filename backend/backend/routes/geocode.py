import logging
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from backend.clients.google_maps import GoogleMapsClient
from backend.container import Container
from backend.exceptions import AddressNotFoundError
from backend.models import GeocodeRequest, GeocodeResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/geocode", status_code=HTTPStatus.CREATED, response_model=GeocodeResponse)
@inject
async def geocode(
    request: GeocodeRequest,
    google_maps_client: GoogleMapsClient = Depends(Provide[Container.google_maps_client]),
):
    try:
        location = await google_maps_client.geocode(request.address)
        return GeocodeResponse(location=location)
    except AddressNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Address not found")
    except Exception as e:
        logger.error(f"Geocoding failed for address '{request.address}': {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unable to geocode address",
        )
