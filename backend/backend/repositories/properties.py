from typing import Callable, List

from sqlmodel import select

from backend.exceptions import DocumentNotFoundError, PropertyNotFoundError
from backend.models import DocumentInfo, PropertyInfo


class PropertyRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    async def insert_property(self, property_data: PropertyInfo) -> PropertyInfo:
        with self._session_factory() as session:
            session.add(property_data)
            session.commit()
            session.refresh(property_data)
            return property_data

    async def list_properties(self) -> List[PropertyInfo]:
        with self._session_factory() as session:
            return list(session.exec(select(PropertyInfo)).all())

    async def get_property(self, property_id: str) -> PropertyInfo:
        with self._session_factory() as session:
            return session.get(PropertyInfo, property_id)

    async def append_document(self, property_id: str, document: DocumentInfo) -> PropertyInfo:
        with self._session_factory() as session:
            prop = session.get(PropertyInfo, property_id)
            prop.documents = (prop.documents or []) + [document]
            session.add(prop)
            session.commit()
            session.refresh(prop)
            return prop

    async def remove_document(self, property_id: str, doc_id: str) -> PropertyInfo:
        with self._session_factory() as session:
            prop = session.get(PropertyInfo, property_id)
            if prop is None:
                raise PropertyNotFoundError(f"Property {property_id} not found")
            documents = prop.documents or []
            updated = [d for d in documents if d.id != doc_id]
            if len(updated) == len(documents):
                raise DocumentNotFoundError(f"Document {doc_id} not found on property {property_id}")
            prop.documents = updated
            session.add(prop)
            session.commit()
            session.refresh(prop)
            return prop
