from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from backend.container import Container
from backend.models import TemplateResponse
from backend.template_loader import TemplateLoader

router = APIRouter()


@router.get("/templates/default", status_code=HTTPStatus.OK)
@inject
async def get_default_template(
    template_loader: TemplateLoader = Depends(Provide[Container.template_loader]),
):
    template = template_loader.read_user_prompt()
    return TemplateResponse(template=template)
