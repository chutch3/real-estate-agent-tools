from typing import Callable, List

from sqlmodel import select

from backend.models import ChatMessage


class ChatMessageRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    async def save_message(self, property_id: str, role: str, content: str) -> ChatMessage:
        with self._session_factory() as session:
            message = ChatMessage(property_id=property_id, role=role, content=content)
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    async def get_history(self, property_id: str) -> List[ChatMessage]:
        with self._session_factory() as session:
            return list(
                session.exec(
                    select(ChatMessage)
                    .where(ChatMessage.property_id == property_id)
                    .order_by(ChatMessage.created_at)
                ).all()
            )
