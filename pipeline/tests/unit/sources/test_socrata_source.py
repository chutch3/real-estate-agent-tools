from datetime import date

import pytest
from pytest_httpserver import HTTPServer
from shapely.geometry import box
from werkzeug.wrappers import Response

from pipeline.sources.socrata import SocrataSource, _map_category

_LOUISVILLE_BBOX = box(-86.035, 37.997, -85.404, 38.375)


class TestSocrataSource:
    @pytest.fixture
    def subject(self, httpserver: HTTPServer) -> SocrataSource:
        return SocrataSource(
            name="louisville-metro-pd",
            dataset_id="4sxa-cwis",
            date_field="date_occured",
            lat_field="latitude",
            lon_field="longitude",
            category_field="offense",
            base_url=httpserver.url_for("").rstrip("/"),
        )

    def test_fetch_returns_geodataframe_with_canonical_schema(
        self, subject: SocrataSource, httpserver: HTTPServer
    ):
        httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(
            [
                {
                    "latitude": "38.25",
                    "longitude": "-85.75",
                    "date_occured": "2025-06-15T00:00:00.000",
                    "offense": "ASSAULT",
                },
            ]
        )

        result = subject.fetch(_LOUISVILLE_BBOX, date(2025, 1, 1), date(2025, 12, 31))

        assert list(result.columns) >= ["lat", "lon", "category", "date", "source"]
        assert len(result) == 1
        assert result.iloc[0]["lat"] == pytest.approx(38.25)
        assert result.iloc[0]["lon"] == pytest.approx(-85.75)
        assert result.iloc[0]["category"] == "violent"
        assert result.iloc[0]["source"] == "louisville-metro-pd"
        assert result.crs.to_epsg() == 4326

    def test_fetch_returns_empty_dataframe_on_empty_response(
        self, subject: SocrataSource, httpserver: HTTPServer
    ):
        httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json([])

        result = subject.fetch(_LOUISVILLE_BBOX, date(2025, 1, 1), date(2025, 12, 31))

        assert len(result) == 0
        assert result.crs.to_epsg() == 4326

    def test_fetch_skips_rows_with_missing_coordinates(
        self, subject: SocrataSource, httpserver: HTTPServer
    ):
        httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(
            [
                {"date_occured": "2025-06-15T00:00:00.000", "offense": "THEFT"},
                {
                    "latitude": "38.25",
                    "longitude": "-85.75",
                    "date_occured": "2025-06-16T00:00:00.000",
                    "offense": "THEFT",
                },
            ]
        )

        result = subject.fetch(_LOUISVILLE_BBOX, date(2025, 1, 1), date(2025, 12, 31))

        assert len(result) == 1

    def test_fetch_sends_app_token_header_when_configured(
        self, httpserver: HTTPServer
    ):
        received_headers: dict[str, str] = {}

        def capture_handler(request):
            received_headers.update(dict(request.headers))
            return Response(b"[]", content_type="application/json")

        httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_handler(
            capture_handler
        )
        source = SocrataSource(
            name="louisville-metro-pd",
            dataset_id="4sxa-cwis",
            date_field="date_occured",
            lat_field="latitude",
            lon_field="longitude",
            category_field="offense",
            base_url=httpserver.url_for("").rstrip("/"),
            app_token="my-secret-token",
        )

        source.fetch(_LOUISVILLE_BBOX, date(2025, 1, 1), date(2025, 12, 31))

        lower_headers = {k.lower(): v for k, v in received_headers.items()}
        assert lower_headers.get("x-app-token") == "my-secret-token"


@pytest.mark.parametrize(
    "offense,expected",
    [
        ("ASSAULT", "violent"),
        ("ASSAULT 4TH DEGREE", "violent"),
        ("ASSAULT - FELONY", "violent"),
        ("HOMICIDE", "violent"),
        ("RAPE", "violent"),
        ("ROBBERY", "violent"),
        ("BURGLARY", "property"),
        ("THEFT", "property"),
        ("MOTOR VEHICLE THEFT", "property"),
        ("VANDALISM/CRIMINAL MISCHIEF", "property"),
        ("ARSON", "property"),
        ("DRUG OFFENSE", "other"),
        ("DUI", "other"),
        ("", "other"),
    ],
)
def test_map_category(offense: str, expected: str) -> None:
    assert _map_category(offense) == expected
