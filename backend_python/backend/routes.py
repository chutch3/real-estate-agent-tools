from http import HTTPStatus

from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from .container import Container
from .models import PostGenerationRequest
from .post_coordinator import PostCoordinator

router = APIRouter()


@router.post("/generate-post", status_code=HTTPStatus.CREATED)
@inject
async def generate_post(
    request: PostGenerationRequest,
    coordinator: PostCoordinator = Depends(Provide[Container.post_coordinator]),
):
    return {
        "post": await coordinator.generate_post(
            address=request.address,
            agent_info=request.agent_info,
            custom_template=request.custom_template,
        )
    }
