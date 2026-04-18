import pytest
from sqlalchemy import create_engine, inspect
from sqlmodel import Session, select

from backend.database import Database
from backend.models import Property


class TestDatabase:
    def test_session_yields_sqlmodel_session(self, subject: Database):
        with subject.session() as session:
            assert isinstance(session, Session)

    def test_session_rollback_on_exception(self, subject: Database):
        property_data = Property(id="rollback-test")
        try:
            with subject.session() as session:
                session.add(property_data)
                raise RuntimeError("forced error")
        except RuntimeError:
            pass

        with subject.session() as session:
            result = session.exec(select(Property)).first()
            assert result is None

    def test_creates_tables_on_init(self, db_url: str):
        Database(url=db_url)
        engine = create_engine(db_url)
        inspector = inspect(engine)
        assert "property" in inspector.get_table_names()

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def subject(self, db_url: str) -> Database:
        return Database(url=db_url)
