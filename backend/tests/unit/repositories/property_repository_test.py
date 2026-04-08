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
    async def test_insert_property_persists_county_fips(
        self,
        subject: PropertyRepository,
        property_info_factory,
        db: Database,
    ):
        property_data = property_info_factory.build()
        property_data.county_fips = "18019"

        await subject.insert_property(property_data)

        with db.session() as session:
            result = session.exec(select(PropertyInfo)).first()
            assert result.county_fips == "18019"

    @pytest.mark.asyncio
    async def test_list_properties(
        self,
        subject: PropertyRepository,
        property_info_factory,
        db: Database,
    ):
        brokerage_1 = "brokerage-1"
        brokerage_2 = "brokerage-2"

        first = property_info_factory.build(brokerage_id=brokerage_1)
        second = property_info_factory.build(brokerage_id=brokerage_1)
        third = property_info_factory.build(brokerage_id=brokerage_2)

        await subject.insert_property(first)
        await subject.insert_property(second)
        await subject.insert_property(third)

        results = await subject.list_properties(brokerage_id=brokerage_1)

        assert len(results) == 2
        assert first in results
        assert second in results
        assert third not in results

    @pytest.mark.asyncio
    async def test_list_county_fips_returns_distinct_fips(
        self,
        subject: PropertyRepository,
        property_info_factory,
    ):
        await subject.insert_property(property_info_factory.build(county_fips="21111"))
        await subject.insert_property(property_info_factory.build(county_fips="21111"))
        await subject.insert_property(property_info_factory.build(county_fips="18019"))
        await subject.insert_property(property_info_factory.build(county_fips=None))

        result = await subject.list_county_fips()

        assert set(result) == {"21111", "18019"}

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
        property_data = property_info_factory.build(documents=None, brokerage_id="brokerage-1")
        await subject.insert_property(property_data)
        doc = DocumentInfo(id="doc-1", filename="listing.pdf")

        result = await subject.append_document(property_data.id, doc, "brokerage-1")

        assert result.documents == [doc]
        with db.session() as session:
            persisted = session.get(PropertyInfo, property_data.id)
            assert persisted.documents == [doc]

    @pytest.mark.asyncio
    async def test_remove_document(self, subject, property_info_factory, db):
        doc1 = DocumentInfo(id="doc-1", filename="listing.pdf")
        doc2 = DocumentInfo(id="doc-2", filename="disclosure.pdf")
        prop = property_info_factory.build(documents=[doc1, doc2], brokerage_id="brokerage-1")
        await subject.insert_property(prop)

        result = await subject.remove_document(prop.id, "doc-1", brokerage_id="brokerage-1")

        assert result.documents == [doc2]
        with db.session() as session:
            persisted = session.get(PropertyInfo, prop.id)
            assert persisted.documents == [doc2]

    @pytest.mark.asyncio
    async def test_remove_document_isolation(self, subject, property_info_factory):
        prop = property_info_factory.build(
            documents=[DocumentInfo(id="doc-1", filename="listing.pdf")], brokerage_id="brokerage-1"
        )
        await subject.insert_property(prop)

        with pytest.raises(PropertyNotFoundError):
            await subject.remove_document(prop.id, "doc-1", brokerage_id="brokerage-2")

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_doc_not_in_property(self, subject, property_info_factory):
        prop = property_info_factory.build(
            documents=[DocumentInfo(id="doc-1", filename="listing.pdf")], brokerage_id="brokerage-1"
        )
        await subject.insert_property(prop)

        with pytest.raises(DocumentNotFoundError):
            await subject.remove_document(prop.id, "nonexistent-doc", "brokerage-1")

    @pytest.mark.asyncio
    async def test_remove_document_raises_when_property_not_found(self, subject):
        with pytest.raises(PropertyNotFoundError):
            await subject.remove_document("nonexistent-property", "doc-1", "brokerage-1")

    @pytest.mark.asyncio
    async def test_update_parcel_nguid(self, subject: PropertyRepository, property_info_factory, db: Database):
        prop = property_info_factory.build(parcel_nguid=None)
        await subject.insert_property(prop)

        await subject.update_parcel_nguid(prop.id, "urn:emergency:uid:gis:PCL:test-nguid:test.in.gov")

        with db.session() as session:
            persisted = session.get(PropertyInfo, prop.id)
            assert persisted.parcel_nguid == "urn:emergency:uid:gis:PCL:test-nguid:test.in.gov"

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> PropertyRepository:
        return test_container.property_repository()
