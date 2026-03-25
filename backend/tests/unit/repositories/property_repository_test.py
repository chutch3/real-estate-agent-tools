import pytest
from sqlmodel import select

from backend.container import Container
from backend.database import Database
from backend.exceptions import DocumentNotFoundError, PropertyNotFoundError
from backend.models import DocumentInfo, PropertyInfo
from backend.repositories.properties import PropertyRepository


class TestPropertyRepository:
    @pytest.mark.asyncio
    async def test_insert_property(
        self,
        subject: PropertyRepository,
        property_info_factory,
        db: Database,
    ):
        property_data = property_info_factory.build()
        await subject.insert_property(property_data)

        with db.session() as session:
            assert session.exec(select(PropertyInfo)).first() == property_data

    @pytest.mark.asyncio
    async def test_list_properties(
        self,
        subject: PropertyRepository,
        property_info_factory,
        db: Database,
    ):
        first = property_info_factory.build()
        second = property_info_factory.build()
        await subject.insert_property(first)
        await subject.insert_property(second)

        results = await subject.list_properties()

        assert len(results) == 2
        assert first in results
        assert second in results

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.mark.asyncio
    async def test_append_document(
        self,
        subject: PropertyRepository,
        property_info_factory,
        db: Database,
    ):
        property_data = property_info_factory.build(documents=None)
        await subject.insert_property(property_data)
        doc = DocumentInfo(id="doc-1", filename="listing.pdf")

        result = await subject.append_document(property_data.id, doc)

        assert result.documents == [doc]
        with db.session() as session:
            persisted = session.get(PropertyInfo, property_data.id)
            assert persisted.documents == [doc]

    @pytest.mark.asyncio
    async def test_remove_document(self, subject, property_info_factory, db):
        doc1 = DocumentInfo(id="doc-1", filename="listing.pdf")
        doc2 = DocumentInfo(id="doc-2", filename="disclosure.pdf")
        prop = property_info_factory.build(documents=[doc1, doc2])
        await subject.insert_property(prop)

        result = await subject.remove_document(prop.id, "doc-1")

        assert result.documents == [doc2]
        with db.session() as session:
            persisted = session.get(PropertyInfo, prop.id)
            assert persisted.documents == [doc2]

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_doc_not_in_property(self, subject, property_info_factory):
        prop = property_info_factory.build(documents=[DocumentInfo(id="doc-1", filename="listing.pdf")])
        await subject.insert_property(prop)

        with pytest.raises(DocumentNotFoundError):
            await subject.remove_document(prop.id, "nonexistent-doc")

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_property_not_found(self, subject):
        with pytest.raises(PropertyNotFoundError):
            await subject.remove_document("nonexistent-property", "doc-1")

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> PropertyRepository:
        return test_container.property_repository()
