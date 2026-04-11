from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import NetSheetNotFoundError
from backend.models import NetSheetResponse, NetSheetScenarioCreate, NetSheetScenarioUpdate, User
from backend.services.net_sheet import NetSheetService

router = APIRouter()


@router.get("/properties/{property_id}/net-sheet", status_code=HTTPStatus.OK, response_model=NetSheetResponse)
@inject
async def get_net_sheet(
    property_id: str,
    current_user: User = Depends(get_current_user),
    net_sheet_service: NetSheetService = Depends(Provide[Container.net_sheet_service]),
):
    try:
        return await net_sheet_service.get_net_sheet(property_id, current_user.brokerage_id)
    except NetSheetNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")


@router.post(
    "/properties/{property_id}/net-sheet/scenarios",
    status_code=HTTPStatus.CREATED,
    response_model=NetSheetResponse,
)
@inject
async def add_net_sheet_scenario(
    property_id: str,
    scenario: NetSheetScenarioCreate,
    current_user: User = Depends(get_current_user),
    net_sheet_service: NetSheetService = Depends(Provide[Container.net_sheet_service]),
):
    try:
        return await net_sheet_service.add_scenario(property_id, current_user.brokerage_id, scenario)
    except NetSheetNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")


@router.patch(
    "/properties/{property_id}/net-sheet/scenarios/{scenario_id}",
    status_code=HTTPStatus.OK,
    response_model=NetSheetResponse,
)
@inject
async def update_net_sheet_scenario(
    property_id: str,
    scenario_id: str,
    update: NetSheetScenarioUpdate,
    current_user: User = Depends(get_current_user),
    net_sheet_service: NetSheetService = Depends(Provide[Container.net_sheet_service]),
):
    try:
        return await net_sheet_service.update_scenario(property_id, current_user.brokerage_id, scenario_id, update)
    except NetSheetNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Scenario not found")


@router.delete(
    "/properties/{property_id}/net-sheet/scenarios/{scenario_id}",
    status_code=HTTPStatus.OK,
    response_model=NetSheetResponse,
)
@inject
async def delete_net_sheet_scenario(
    property_id: str,
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    net_sheet_service: NetSheetService = Depends(Provide[Container.net_sheet_service]),
):
    try:
        return await net_sheet_service.delete_scenario(property_id, current_user.brokerage_id, scenario_id)
    except NetSheetNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Scenario not found")
