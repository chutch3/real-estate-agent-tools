import pytest

from backend.container import Container
from backend.database import Database
from backend.models import Brokerage, User
from backend.repositories.user import UserRepository


class TestUserRepository:
    def test_create_returns_user_with_id(self, subject: UserRepository, brokerage: Brokerage):
        user = User(email="agent@acme.com", hashed_password="hashed", role="AGENT", brokerage_id=brokerage.id)

        result = subject.create(user)

        assert result.id is not None
        assert result.email == "agent@acme.com"
        assert result.brokerage_id == brokerage.id

    def test_create_persists_user(self, subject: UserRepository, brokerage: Brokerage):
        user = User(email="agent@acme.com", hashed_password="hashed", role="AGENT", brokerage_id=brokerage.id)

        created = subject.create(user)
        fetched = subject.get_by_id(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.email == "agent@acme.com"

    def test_get_by_email_returns_user(self, subject: UserRepository, brokerage: Brokerage):
        user = User(email="agent@acme.com", hashed_password="hashed", role="AGENT", brokerage_id=brokerage.id)
        subject.create(user)

        result = subject.get_by_email("agent@acme.com")

        assert result is not None
        assert result.email == "agent@acme.com"

    def test_get_by_email_returns_none_when_not_found(self, subject: UserRepository):
        result = subject.get_by_email("nobody@nowhere.com")

        assert result is None

    def test_get_by_id_returns_none_when_not_found(self, subject: UserRepository):
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
    def brokerage(self, test_container: Container, db: Database) -> Brokerage:
        return test_container.brokerage_repository().create(Brokerage(name="Test Brokerage"))

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> UserRepository:
        return test_container.user_repository()
