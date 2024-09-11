from http import HTTPStatus
from http.client import HTTPException

from backend.clients.google_maps import GoogleMapsClient
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from .container import Container
from .exceptions import AddressNotFoundError, PropertyNotFoundError
from .models import GeocodeRequest, GeocodeResponse, PostGenerationRequest
from .post_coordinator import PostCoordinator

router = APIRouter()


@router.post("/generate-post", status_code=HTTPStatus.CREATED)
@inject
async def generate_post(
    request: PostGenerationRequest,
    coordinator: PostCoordinator = Depends(Provide[Container.post_coordinator]),
):
    """
    Generate a post for a property.

    Args:
        request (PostGenerationRequest): The request object.
        coordinator (PostCoordinator): The post coordinator.

    Returns:
        dict: The generated post.
    """
    try:
        post = await coordinator.generate_post(
            address=request.address,
            agent_info=request.agent_info,
            custom_template=request.custom_template,
        )
        return {"post": post}
    except PropertyNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Property not found"
        )


@router.post(
    "/geocode",
    status_code=HTTPStatus.CREATED,
    response_model=GeocodeResponse,
)
@inject
async def geocode(
    request: GeocodeRequest,
    google_maps_client: GoogleMapsClient = Depends(
        Provide[Container.google_maps_client]
    ),
):
    """
    Geocode an address.

    Args:
        request (GeocodeRequest): The request object.
        google_maps_client (GoogleMapsClient): The Google Maps client.

    Returns:
        GeocodeResponse: The response object.
    """
    try:
        location = await google_maps_client.geocode(request.address)
        return GeocodeResponse(location=location)
    except AddressNotFoundError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Address not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Unable to geocode address",
        )
