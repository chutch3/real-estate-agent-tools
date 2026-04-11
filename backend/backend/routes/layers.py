from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from backend.container import Container
from backend.services.layer import LayerService

router = APIRouter()


@router.get("/layers", status_code=HTTPStatus.OK)
@inject
async def get_layers(
    county_fips: str | None = None,
    layer_service: LayerService = Depends(Provide[Container.layer_service]),
):
    return await layer_service.get_layers(county_fips=county_fips)


@router.get("/layers/{layer_id}/tiles/{z}/{x}/{y}", status_code=HTTPStatus.OK)
@inject
async def get_layer_tile(
    layer_id: str,
    z: int,
    x: int,
    y: int,
    layer_service: LayerService = Depends(Provide[Container.layer_service]),
):
    tile_bytes = await layer_service.get_tile(layer_id=layer_id, z=z, x=x, y=y)
    return Response(
        content=tile_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=604800"},
    )
