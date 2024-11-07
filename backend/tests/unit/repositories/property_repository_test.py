from typing import Container

import pytest
from sqlmodel import Session, select
from tests.factories import PropertyInfoFactory

from backend.models import PropertyInfo
from backend.repositories.properties import PropertyRepository


class TestPropertyRepository:
    @pytest.mark.asyncio
    async def test_insert_property(
        self,
        subject: PropertyRepository,
        property_info_factory: PropertyInfoFactory,
        test_db_session: Session,
    ):
        property_data = property_info_factory.build()
        await subject.insert_property(property_data)

        assert test_db_session.exec(select(PropertyInfo)).first() == property_data

    @pytest.fixture(scope="class", autouse=True)
    def test_db_engine(self, test_container: Container, random_database_name):
        test_container.config.db.uri.from_value(f"sqlite:///{random_database_name}.db")
        return test_container.db_engine()

    @pytest.fixture()
    def test_db_session(self, test_container: Container):
        yield test_container.db_session()

    @pytest.fixture
    def subject(self, test_container: Container):
        return test_container.property_repository()
