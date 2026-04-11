from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pymilvus.exceptions import MilvusException

from backend.container import Container
from backend.models import ChatMessageResponse, ChatRequest
from backend.services.chat import ChatService

router = APIRouter()


@router.post("/properties/{property_id}/chat", status_code=HTTPStatus.OK)
@inject
async def chat(
    property_id: str,
    request: ChatRequest,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    try:
        messages = await chat_service.prepare_chat_messages(property_id, request.message)
    except MilvusException:
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Document search unavailable")

    async def event_generator():
        async for chunk in chat_service.stream_response(property_id, messages):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/properties/{property_id}/chat",
    status_code=HTTPStatus.OK,
    response_model=list[ChatMessageResponse],
)
@inject
async def get_chat_history(
    property_id: str,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    return await chat_service.get_history(property_id)
