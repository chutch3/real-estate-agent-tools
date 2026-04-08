import pytest

from backend.container import Container
from backend.database import Database
from backend.models import Brokerage
from backend.repositories.brokerage import BrokerageRepository


class TestBrokerageRepository:
    def test_create_returns_brokerage_with_id(self, subject: BrokerageRepository):
        brokerage = Brokerage(name="Acme Realty", contact_info="123 Main St")

        result = subject.create(brokerage)

        assert result.id is not None
        assert result.name == "Acme Realty"
        assert result.contact_info == "123 Main St"

    def test_create_persists_brokerage(self, subject: BrokerageRepository):
        brokerage = Brokerage(name="Acme Realty")

        created = subject.create(brokerage)
        fetched = subject.get_by_id(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "Acme Realty"

    def test_get_by_id_returns_none_when_not_found(self, subject: BrokerageRepository):
        result = subject.get_by_id("nonexistent-id")

        assert result is None

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> BrokerageRepository:
        return test_container.brokerage_repository()
