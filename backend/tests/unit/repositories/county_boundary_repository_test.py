import pytest

from backend.container import Container
from backend.database import Database
from backend.models import CountyBoundary
from backend.repositories.county_boundary import CountyBoundaryRepository

_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[-86.0, 38.0], [-85.4, 38.0], [-85.4, 38.4], [-86.0, 38.4], [-86.0, 38.0]]],
}


class TestCountyBoundaryRepository:
    def test_get_by_fips_returns_none_when_not_found(self, subject: CountyBoundaryRepository):
        result = subject.get_by_fips("99999")
        assert result is None

    def test_upsert_stores_boundary(self, subject: CountyBoundaryRepository, db: Database):
        boundary = CountyBoundary(fips="21111", geometry=_POLYGON)

        result = subject.upsert(boundary)

        assert result.fips == "21111"
        assert result.geometry == _POLYGON

    def test_get_by_fips_returns_stored_boundary(self, subject: CountyBoundaryRepository):
        subject.upsert(CountyBoundary(fips="21111", geometry=_POLYGON))

        result = subject.get_by_fips("21111")

        assert result is not None
        assert result.fips == "21111"
        assert result.geometry == _POLYGON

    def test_upsert_updates_existing_boundary(self, subject: CountyBoundaryRepository):
        subject.upsert(CountyBoundary(fips="21111", geometry=_POLYGON))
        updated_polygon = {
            "type": "Polygon",
            "coordinates": [[[-87.0, 38.0], [-86.0, 38.0], [-86.0, 39.0], [-87.0, 39.0], [-87.0, 38.0]]],
        }

        result = subject.upsert(CountyBoundary(fips="21111", geometry=updated_polygon))

        assert result.geometry == updated_polygon
        assert subject.get_by_fips("21111").geometry == updated_polygon

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> CountyBoundaryRepository:
        return test_container.county_boundary_repository()
