import pytest
from pytest_httpserver import HTTPServer

from pipeline.geocoding.census import CensusGeocoder


def _match_row(idx: int, lon: float, lat: float) -> str:
    return (
        f'{idx},"100 N 4TH ST, LOUISVILLE, KY, 40202",'
        f'Match,Exact,"100 N 4TH ST, LOUISVILLE, KY, 40202",'
        f'"{lon},{lat}",123456,R\n'
    )


def _no_match_row(idx: int) -> str:
    return f'{idx},"999 FAKE ST, LOUISVILLE, KY, 40202",No_Match,,,,,\n'


class TestCensusGeocoder:
    @pytest.fixture
    def subject(self, httpserver: HTTPServer) -> CensusGeocoder:
        return CensusGeocoder(url=httpserver.url_for("/geocoder"))

    def _expect(self, httpserver: HTTPServer, body: str) -> None:
        httpserver.expect_request("/geocoder").respond_with_data(
            body, content_type="text/plain"
        )

    def test_geocode_returns_lat_lon_for_matched_addresses(self, subject, httpserver):
        self._expect(httpserver, _match_row(0, -85.7573, 38.2567))

        result = subject.geocode([(0, "100 N 4TH ST", "LOUISVILLE", "KY", "40202")])

        assert result == {0: (pytest.approx(38.2567), pytest.approx(-85.7573))}

    def test_geocode_omits_unmatched_addresses(self, subject, httpserver):
        self._expect(httpserver, _no_match_row(0))

        result = subject.geocode([(0, "999 FAKE ST", "LOUISVILLE", "KY", "40202")])

        assert result == {}

    def test_geocode_handles_mixed_match_and_no_match(self, subject, httpserver):
        self._expect(
            httpserver,
            _match_row(1, -85.7573, 38.2567) + _no_match_row(2),
        )

        result = subject.geocode([
            (1, "100 N 4TH ST", "LOUISVILLE", "KY", "40202"),
            (2, "999 FAKE ST", "LOUISVILLE", "KY", "40202"),
        ])

        assert 1 in result
        assert 2 not in result

    def test_geocode_handles_none_address_fields(self, subject, httpserver):
        self._expect(httpserver, _no_match_row(0))

        result = subject.geocode([(0, None, None, None, None)])

        assert result == {}
