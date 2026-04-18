from collections.abc import Callable

from sqlmodel import select

from backend.models import Document


class DocumentRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_by_property_id(self, property_id: str) -> list[Document]:
        with self._session_factory() as session:
            return list(session.exec(select(Document).where(Document.property_id == property_id)).all())

    def insert_many(self, docs: list[Document]) -> None:
        if not docs:
            return
        with self._session_factory() as session:
            session.add_all(docs)
            session.commit()

    def delete(self, doc_id: str) -> None:
        with self._session_factory() as session:
            doc = session.get(Document, doc_id)
            if doc:
                session.delete(doc)
                session.commit()
