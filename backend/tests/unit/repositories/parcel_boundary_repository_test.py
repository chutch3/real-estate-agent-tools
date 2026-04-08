import pytest

from backend.container import Container
from backend.database import Database
from backend.models import ParcelBoundary
from backend.repositories.parcel_boundary import ParcelBoundaryRepository

_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [-86.1590, 39.7690],
            [-86.1580, 39.7690],
            [-86.1580, 39.7680],
            [-86.1590, 39.7680],
            [-86.1590, 39.7690],
        ]
    ],
}


class TestParcelBoundaryRepository:
    def test_get_by_nguid_returns_none_when_not_found(self, subject: ParcelBoundaryRepository):
        result = subject.get_by_nguid("urn:emergency:uid:gis:PCL:nonexistent")

        assert result is None

    def test_upsert_stores_boundary(self, subject: ParcelBoundaryRepository):
        boundary = ParcelBoundary(nguid="urn:emergency:uid:gis:PCL:test-nguid", geometry=_POLYGON)

        result = subject.upsert(boundary)

        assert result.nguid == "urn:emergency:uid:gis:PCL:test-nguid"
        assert result.geometry == _POLYGON

    def test_get_by_nguid_returns_stored_boundary(self, subject: ParcelBoundaryRepository):
        subject.upsert(ParcelBoundary(nguid="urn:emergency:uid:gis:PCL:test-nguid", geometry=_POLYGON))

        result = subject.get_by_nguid("urn:emergency:uid:gis:PCL:test-nguid")

        assert result is not None
        assert result.nguid == "urn:emergency:uid:gis:PCL:test-nguid"
        assert result.geometry == _POLYGON

    def test_upsert_updates_existing_boundary(self, subject: ParcelBoundaryRepository):
        subject.upsert(ParcelBoundary(nguid="urn:emergency:uid:gis:PCL:test-nguid", geometry=_POLYGON))
        updated_polygon = {
            "type": "Polygon",
            "coordinates": [[[-86.2, 39.8], [-86.1, 39.8], [-86.1, 39.7], [-86.2, 39.7], [-86.2, 39.8]]],
        }

        result = subject.upsert(ParcelBoundary(nguid="urn:emergency:uid:gis:PCL:test-nguid", geometry=updated_polygon))

        assert result.geometry == updated_polygon
        assert subject.get_by_nguid("urn:emergency:uid:gis:PCL:test-nguid").geometry == updated_polygon

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> ParcelBoundaryRepository:
        return test_container.parcel_boundary_repository()
