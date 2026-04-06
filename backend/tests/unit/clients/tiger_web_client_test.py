import pytest
from pytest_httpserver import HTTPServer

from backend.clients.tiger import TigerWebClient

_ARCGIS_POLYGON_RESPONSE = {
    "features": [
        {
            "geometry": {
                "rings": [
                    [
                        [-86.035, 37.997],
                        [-85.404, 37.997],
                        [-85.404, 38.375],
                        [-86.035, 38.375],
                        [-86.035, 37.997],
                    ]
                ],
                "spatialReference": {"wkid": 4326},
            }
        }
    ]
}

_EXPECTED_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [-86.035, 37.997],
            [-85.404, 37.997],
            [-85.404, 38.375],
            [-86.035, 38.375],
            [-86.035, 37.997],
        ]
    ],
}


class TestTigerWebClient:
    @pytest.mark.asyncio
    async def test_get_county_polygon_returns_geojson_geometry(self, httpserver: HTTPServer):
        httpserver.expect_request("/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query").respond_with_json(
            _ARCGIS_POLYGON_RESPONSE
        )

        client = TigerWebClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_polygon("21111")

        assert result == _EXPECTED_POLYGON

    @pytest.mark.asyncio
    async def test_get_county_polygon_returns_none_when_no_features(self, httpserver: HTTPServer):
        httpserver.expect_request("/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query").respond_with_json(
            {"features": []}
        )

        client = TigerWebClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_polygon("99999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_county_polygon_passes_fips_in_query(self, httpserver: HTTPServer):
        httpserver.expect_request(
            "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query",
            query_string="f=json&where=GEOID+LIKE+'21111%25'&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*&orderByFields=BASENAME&resultRecordCount=1&outSR=4326",
        ).respond_with_json(_ARCGIS_POLYGON_RESPONSE)

        client = TigerWebClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_polygon("21111")

        assert result is not None
