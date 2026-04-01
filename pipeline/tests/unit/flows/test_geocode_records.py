from unittest.mock import MagicMock

import geopandas as gpd
import pytest
from prefect import flow
from prefect.testing.utilities import prefect_test_harness
from shapely.geometry import Point

from pipeline.geocoding.base import Geocoder
from pipeline.flows.crime_heatmap import geocode_records


@pytest.fixture(scope="module")
def prefect_harness():
    with prefect_test_harness():
        yield


def _make_frame_with_geometry() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        [{"lat": 38.25, "lon": -85.75, "category": "violent", "date": "2025-01-01",
          "source": "test", "geometry": Point(-85.75, 38.25)}],
        geometry="geometry",
        crs="EPSG:4326",
    )


def _make_frame_without_geometry() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        [{"lat": None, "lon": None, "category": "violent", "date": "2025-01-01",
          "source": "test", "address": "100 BLOCK N 4TH ST", "city": "LOUISVILLE",
          "zip_code": "40202", "state": "KY", "geometry": None}],
        geometry="geometry",
        crs="EPSG:4326",
    )


class TestGeocodeRecords:
    @pytest.fixture
    def geocoder(self) -> MagicMock:
        return MagicMock(spec=Geocoder)

    def _run(self, frame: gpd.GeoDataFrame, geocoder: MagicMock) -> gpd.GeoDataFrame:
        @flow
        def _flow():
            return geocode_records(frame, geocoder)
        return _flow()

    def test_skips_records_that_already_have_geometry(self, prefect_harness, geocoder):
        frame = _make_frame_with_geometry()

        result = self._run(frame, geocoder)

        assert len(result) == 1
        assert result.iloc[0]["lat"] == pytest.approx(38.25)
        geocoder.geocode.assert_not_called()

    def test_geocodes_records_without_geometry(self, prefect_harness, geocoder):
        geocoder.geocode.return_value = {0: (38.2567, -85.7573)}
        frame = _make_frame_without_geometry()

        result = self._run(frame, geocoder)

        assert len(result) == 1
        assert result.iloc[0]["lat"] == pytest.approx(38.2567)
        assert result.iloc[0]["lon"] == pytest.approx(-85.7573)
        assert result.geometry.notna().all()

    def test_drops_records_that_could_not_be_geocoded(self, prefect_harness, geocoder):
        geocoder.geocode.return_value = {}
        frame = _make_frame_without_geometry()

        result = self._run(frame, geocoder)

        assert len(result) == 0

    def test_preserves_already_geocoded_records_when_some_fail(self, prefect_harness, geocoder):
        geocoder.geocode.return_value = {1: (38.2567, -85.7573)}
        frame = gpd.GeoDataFrame(
            [
                {"lat": 38.25, "lon": -85.75, "category": "violent", "date": "2025-01-01",
                 "source": "test", "geometry": Point(-85.75, 38.25)},
                {"lat": None, "lon": None, "category": "violent", "date": "2025-01-01",
                 "source": "test", "address": "100 BLOCK N 4TH ST", "city": "LOUISVILLE",
                 "zip_code": "40202", "state": "KY", "geometry": None},
                {"lat": None, "lon": None, "category": "property", "date": "2025-01-02",
                 "source": "test", "address": "999 FAKE ST", "city": "LOUISVILLE",
                 "zip_code": "40202", "state": "KY", "geometry": None},
            ],
            geometry="geometry",
            crs="EPSG:4326",
        )

        result = self._run(frame, geocoder)

        assert len(result) == 2

    def test_passes_address_fields_to_geocoder(self, prefect_harness, geocoder):
        geocoder.geocode.return_value = {}
        frame = _make_frame_without_geometry()

        self._run(frame, geocoder)

        geocoder.geocode.assert_called_once()
        addresses = geocoder.geocode.call_args[0][0]
        assert len(addresses) == 1
        _id, street, city, state, zip_code = addresses[0]
        assert street == "100 BLOCK N 4TH ST"
        assert city == "LOUISVILLE"
        assert state == "KY"
        assert zip_code == "40202"

    def test_returns_empty_frame_unchanged(self, prefect_harness, geocoder):
        frame = gpd.GeoDataFrame(
            columns=["lat", "lon", "category", "date", "source", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )

        result = self._run(frame, geocoder)

        assert len(result) == 0
        geocoder.geocode.assert_not_called()
