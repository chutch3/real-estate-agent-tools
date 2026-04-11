from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from backend.container import Container
from backend.services.property import PropertyService

router = APIRouter()


@router.get("/internal/counties", status_code=HTTPStatus.OK)
@inject
async def get_internal_counties(
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    fips_list = await property_service.list_county_fips()
    return {"county_fips": fips_list}
