from datetime import date

import pytest
from pytest_httpserver import HTTPServer
from shapely.geometry import box

from pipeline.sources.arcgis import ArcGISFeatureSource, _map_nibrs_category

_LOUISVILLE_BBOX = box(-86.035, 37.997, -85.404, 38.375)

_DATE_FROM = date(2025, 1, 1)
_DATE_TO = date(2025, 1, 31)

# 2025-01-15 00:00:00 UTC in milliseconds
_JAN_15_MS = 1736899200000


def _make_response(features: list, exceeded: bool = False) -> dict:
    return {"features": features, "exceededTransferLimit": exceeded}


def _make_feature(
    date_ms: int = _JAN_15_MS,
    offense: str = "13A AGGRAVATED ASSAULT",
    address: str = "100 BLOCK N 4TH ST",
    city: str = "LOUISVILLE",
    zip_code: str = "40202",
) -> dict:
    return {
        "attributes": {
            "date_occurred": date_ms,
            "offense_classification": offense,
            "block_address": address,
            "city": city,
            "zip_code": zip_code,
        }
    }


class TestArcGISFeatureSource:
    @pytest.fixture
    def subject(self, httpserver: HTTPServer) -> ArcGISFeatureSource:
        return ArcGISFeatureSource(
            name="louisville-metro-pd",
            service_url=httpserver.url_for("/rest/services/crime/FeatureServer/0").rstrip("/"),
            date_field="date_occurred",
            category_field="offense_classification",
            address_field="block_address",
            city_field="city",
            zip_field="zip_code",
            state_code="KY",
        )

    def _expect(self, httpserver: HTTPServer, body: dict) -> None:
        httpserver.expect_request("/rest/services/crime/FeatureServer/0/query").respond_with_json(body)

    def test_fetch_returns_records_with_address_fields(self, subject, httpserver):
        self._expect(httpserver, _make_response([_make_feature()]))

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert len(result) == 1
        assert result.iloc[0]["address"] == "100 BLOCK N 4TH ST"
        assert result.iloc[0]["city"] == "LOUISVILLE"
        assert result.iloc[0]["zip_code"] == "40202"
        assert result.iloc[0]["state"] == "KY"
        assert result.iloc[0]["source"] == "louisville-metro-pd"

    def test_fetch_returns_records_with_no_geometry(self, subject, httpserver):
        self._expect(httpserver, _make_response([_make_feature()]))

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert result.geometry.isna().all()

    def test_fetch_maps_category_from_offense_classification(self, subject, httpserver):
        self._expect(
            httpserver,
            _make_response(
                [
                    _make_feature(offense="13A AGGRAVATED ASSAULT"),
                    _make_feature(offense="220 BURGLARY/BREAKING & ENTERING"),
                    _make_feature(offense="56 ALL OTHER OFFENSES"),
                ]
            ),
        )

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert list(result["category"]) == ["violent", "property", "other"]

    def test_fetch_converts_epoch_ms_to_date_string(self, subject, httpserver):
        self._expect(httpserver, _make_response([_make_feature(date_ms=_JAN_15_MS)]))

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert result.iloc[0]["date"] == "2025-01-15"

    def test_fetch_returns_empty_dataframe_when_no_features(self, subject, httpserver):
        self._expect(httpserver, _make_response([]))

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert len(result) == 0
        assert result.crs.to_epsg() == 4326

    def test_fetch_paginates_when_transfer_limit_exceeded(self, subject, httpserver):
        httpserver.expect_ordered_request("/rest/services/crime/FeatureServer/0/query").respond_with_json(
            _make_response([_make_feature()], exceeded=True)
        )
        httpserver.expect_ordered_request("/rest/services/crime/FeatureServer/0/query").respond_with_json(
            _make_response([_make_feature()], exceeded=False)
        )

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert len(result) == 2

    def test_fetch_has_correct_crs(self, subject, httpserver):
        self._expect(httpserver, _make_response([_make_feature()]))

        result = subject.fetch(_LOUISVILLE_BBOX, _DATE_FROM, _DATE_TO)

        assert result.crs.to_epsg() == 4326


@pytest.mark.parametrize(
    "offense,expected",
    [
        ("13A AGGRAVATED ASSAULT", "violent"),
        ("09A MURDER AND NONNEGLIGENT MANSLAUGHTER", "violent"),
        ("120 ROBBERY", "violent"),
        ("11A RAPE", "violent"),
        ("13B SIMPLE ASSAULT", "violent"),
        ("220 BURGLARY/BREAKING & ENTERING", "property"),
        ("23H ALL OTHER LARCENY", "property"),
        ("290 DESTRUCTION/DAMAGE/VANDALISM OF PROPERTY", "property"),
        ("240 MOTOR VEHICLE THEFT", "property"),
        ("200 ARSON", "property"),
        ("56 ALL OTHER OFFENSES", "other"),
        ("35A DRUG/NARCOTIC VIOLATIONS", "other"),
        ("", "other"),
        (None, "other"),
    ],
)
def test_map_nibrs_category(offense: str, expected: str) -> None:
    assert _map_nibrs_category(offense) == expected
