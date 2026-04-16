import pytest
from pytest_httpserver import HTTPServer

from backend.clients.arcgis_parcels import ArcGISParcelsClient

_ARCGIS_PARCEL_RESPONSE = {
    "features": [
        {
            "type": "Feature",
            "geometry": {
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
            },
            "properties": {
                "nguid": "urn:emergency:uid:gis:PCL:test-parcel-nguid:test.in.gov",
                "state_parcel_id": "102403200259000013",
            },
        }
    ]
}

_EXPECTED_RESULT = {
    "nguid": "urn:emergency:uid:gis:PCL:test-parcel-nguid:test.in.gov",
    "state_parcel_id": "102403200259000013",
    "geometry": {
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
    },
}


class TestArcGISParcelsClient:
    @pytest.mark.asyncio
    async def test_get_parcel_returns_nguid_and_geometry(self, subject: ArcGISParcelsClient, httpserver: HTTPServer):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)

        result = await subject.get_parcel(39.7684, -86.1581)

        assert result == _EXPECTED_RESULT

    @pytest.mark.asyncio
    async def test_get_parcel_returns_none_when_no_features(self, subject: ArcGISParcelsClient, httpserver: HTTPServer):
        httpserver.expect_request("/query").respond_with_json({"features": []})

        result = await subject.get_parcel(39.7684, -86.1581)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_parcel_passes_lat_lon_as_point_geometry(
        self, subject: ArcGISParcelsClient, httpserver: HTTPServer
    ):
        httpserver.expect_request(
            "/query",
            query_string="geometry=-86.1581,39.7684&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&outFields=nguid,state_parcel_id&returnGeometry=true&f=geojson",
        ).respond_with_json(_ARCGIS_PARCEL_RESPONSE)

        result = await subject.get_parcel(39.7684, -86.1581)

        assert result is not None

    @pytest.fixture
    def subject(self, httpserver: HTTPServer) -> ArcGISParcelsClient:
        return ArcGISParcelsClient(base_url=httpserver.url_for("").rstrip("/"))
