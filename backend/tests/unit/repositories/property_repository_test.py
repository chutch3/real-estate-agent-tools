import pytest

from backend.container import Container
from backend.database import Database
from backend.models import Property
from backend.repositories.properties import PropertyRepository


class TestPropertyRepository:
    def test_insert_persists_property(self, subject: PropertyRepository, db: Database):
        prop = Property(city="Jeffersonville", state="IN")

        result = subject.insert(prop)

        with db.session() as session:
            persisted = session.get(Property, result.id)
        assert persisted is not None
        assert persisted.city == "Jeffersonville"

    def test_insert_assigns_id(self, subject: PropertyRepository):
        prop = Property(city="Louisville")

        result = subject.insert(prop)

        assert result.id is not None

    def test_get_returns_property(self, subject: PropertyRepository):
        prop = Property(state="IN")
        saved = subject.insert(prop)

        result = subject.get(saved.id)

        assert result is not None
        assert result.id == saved.id
        assert result.state == "IN"

    def test_get_returns_none_when_not_found(self, subject: PropertyRepository):
        result = subject.get("nonexistent-id")

        assert result is None

    def test_list_county_fips_returns_distinct(self, subject: PropertyRepository):
        subject.insert(Property(county_fips="21111"))
        subject.insert(Property(county_fips="21111"))
        subject.insert(Property(county_fips="18019"))
        subject.insert(Property(county_fips=None))

        result = subject.list_county_fips()

        assert set(result) == {"21111", "18019"}

    def test_list_county_fips_returns_empty_when_no_properties(self, subject: PropertyRepository):
        result = subject.list_county_fips()

        assert result == []

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> PropertyRepository:
        return test_container.property_repository()
