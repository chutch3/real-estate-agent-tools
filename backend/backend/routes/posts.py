import logging
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from backend.auth import get_current_user
from backend.container import Container
from backend.exceptions import PropertyNotFoundError
from backend.models import PostGenerationRequest, PostGenerationResponse, User
from backend.post_coordinator import PostCoordinator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/posts", status_code=HTTPStatus.CREATED)
@inject
async def generate_post(
    request: PostGenerationRequest,
    current_user: User = Depends(get_current_user),
    coordinator: PostCoordinator = Depends(Provide[Container.post_coordinator]),
):
    try:
        post = await coordinator.generate_post(
            property_id=request.property_id,
            brokerage_id=current_user.brokerage_id,
            agent_info=request.agent_info,
            custom_template=request.custom_template,
        )
        return PostGenerationResponse(post=post)
    except PropertyNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Property not found")
