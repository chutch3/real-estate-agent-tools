import json
from pathlib import Path

import pytest
import yaml

from pipeline.regions.loader import load_region, load_region_by_fips
from pipeline.sources.arcgis import ArcGISFeatureSource
from pipeline.sources.socrata import SocrataSource

_SIMPLE_POLYGON_COORDS = [[-86.0, 38.0], [-85.5, 38.0], [-85.5, 38.4], [-86.0, 38.4], [-86.0, 38.0]]

_SOCRATA_SPEC = {
    "name": "test-pd",
    "type": "socrata",
    "domain": "data.test.gov",
    "dataset_id": "test-abc",
    "date_field": "date",
    "lat_field": "lat",
    "lon_field": "lon",
    "category_field": "offense",
    "status": "active",
}


def _write_region(region_dir: Path, polygon_coords: list, sources: list) -> None:
    region_dir.mkdir()
    (region_dir / "region.geojson").write_text(
        json.dumps(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [polygon_coords]},
                "properties": {},
            }
        )
    )
    (region_dir / "sources.yml").write_text(yaml.dump({"sources": sources}))


def test_load_region_returns_correct_slug(tmp_path: Path) -> None:
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [_SOCRATA_SPEC])

    region = load_region("test-region", regions_dir=tmp_path)

    assert region.slug == "test-region"


def test_load_region_loads_polygon_from_geojson(tmp_path: Path) -> None:
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [_SOCRATA_SPEC])

    region = load_region("test-region", regions_dir=tmp_path)

    minx, miny, maxx, maxy = region.polygon.bounds
    assert minx == pytest.approx(-86.0)
    assert miny == pytest.approx(38.0)
    assert maxx == pytest.approx(-85.5)
    assert maxy == pytest.approx(38.4)


def test_load_region_builds_socrata_source_from_active_spec(tmp_path: Path) -> None:
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [_SOCRATA_SPEC])

    region = load_region("test-region", regions_dir=tmp_path)

    assert len(region.sources) == 1
    source = region.sources[0]
    assert isinstance(source, SocrataSource)
    assert source.name == "test-pd"
    assert source.dataset_id == "test-abc"
    assert source.base_url == "https://data.test.gov"


def test_load_region_excludes_pending_sources(tmp_path: Path) -> None:
    pending_spec = {**_SOCRATA_SPEC, "name": "pending-source", "status": "pending"}
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [_SOCRATA_SPEC, pending_spec])

    region = load_region("test-region", regions_dir=tmp_path)

    assert len(region.sources) == 1
    assert region.sources[0].name == "test-pd"


def test_load_region_returns_no_sources_when_all_pending(tmp_path: Path) -> None:
    pending_spec = {**_SOCRATA_SPEC, "status": "pending"}
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [pending_spec])

    region = load_region("test-region", regions_dir=tmp_path)

    assert region.sources == []


def test_load_region_raises_when_slug_not_found(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Region not found"):
        load_region("nonexistent", regions_dir=tmp_path)


def test_load_region_raises_for_unknown_source_type(tmp_path: Path) -> None:
    unknown_spec = {**_SOCRATA_SPEC, "type": "csv"}
    _write_region(tmp_path / "test-region", _SIMPLE_POLYGON_COORDS, [unknown_spec])

    with pytest.raises(ValueError, match="Unknown source type"):
        load_region("test-region", regions_dir=tmp_path)


_TIGER_COUNTY_PATH = "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"

_TIGER_COUNTY_RESPONSE = {
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
                ]
            }
        }
    ]
}

_ARCGIS_SPEC = {
    "name": "test-pd",
    "type": "arcgis",
    "service_url": "https://example.com/FeatureServer/0",
    "date_field": "date_occurred",
    "category_field": "offense_classification",
    "address_field": "block_address",
    "city_field": "city",
    "zip_field": "zip_code",
    "state_code": "KY",
    "status": "active",
}


def _write_sources_config(path: Path, config: dict) -> None:
    path.write_text(yaml.dump(config))


def test_load_region_by_fips_uses_fips_as_slug(tmp_path, httpserver) -> None:
    httpserver.expect_request(_TIGER_COUNTY_PATH).respond_with_json(_TIGER_COUNTY_RESPONSE)
    config_path = tmp_path / "sources_config.yml"
    _write_sources_config(config_path, {"21111": [_ARCGIS_SPEC]})

    region = load_region_by_fips(
        "21111",
        tiger_base_url=httpserver.url_for("").rstrip("/"),
        sources_config_path=config_path,
    )

    assert region.slug == "21111"


def test_load_region_by_fips_fetches_polygon_from_tigerweb(tmp_path, httpserver) -> None:
    httpserver.expect_request(_TIGER_COUNTY_PATH).respond_with_json(_TIGER_COUNTY_RESPONSE)
    config_path = tmp_path / "sources_config.yml"
    _write_sources_config(config_path, {"21111": [_ARCGIS_SPEC]})

    region = load_region_by_fips(
        "21111",
        tiger_base_url=httpserver.url_for("").rstrip("/"),
        sources_config_path=config_path,
    )

    minx, miny, maxx, maxy = region.polygon.bounds
    assert minx == pytest.approx(-86.035)
    assert miny == pytest.approx(37.997)
    assert maxx == pytest.approx(-85.404)
    assert maxy == pytest.approx(38.375)


def test_load_region_by_fips_builds_sources_from_config(tmp_path, httpserver) -> None:
    httpserver.expect_request(_TIGER_COUNTY_PATH).respond_with_json(_TIGER_COUNTY_RESPONSE)
    config_path = tmp_path / "sources_config.yml"
    _write_sources_config(config_path, {"21111": [_ARCGIS_SPEC]})

    region = load_region_by_fips(
        "21111",
        tiger_base_url=httpserver.url_for("").rstrip("/"),
        sources_config_path=config_path,
    )

    assert len(region.sources) == 1
    assert isinstance(region.sources[0], ArcGISFeatureSource)
    assert region.sources[0].name == "test-pd"


def test_load_region_by_fips_returns_empty_sources_when_fips_not_in_config(tmp_path, httpserver) -> None:
    httpserver.expect_request(_TIGER_COUNTY_PATH).respond_with_json(_TIGER_COUNTY_RESPONSE)
    config_path = tmp_path / "sources_config.yml"
    _write_sources_config(config_path, {})

    region = load_region_by_fips(
        "99999",
        tiger_base_url=httpserver.url_for("").rstrip("/"),
        sources_config_path=config_path,
    )

    assert region.sources == []


def test_load_region_by_fips_returns_none_when_tigerweb_has_no_features(tmp_path, httpserver) -> None:
    httpserver.expect_request(_TIGER_COUNTY_PATH).respond_with_json({"features": []})
    config_path = tmp_path / "sources_config.yml"
    _write_sources_config(config_path, {"99999": []})

    result = load_region_by_fips(
        "99999",
        tiger_base_url=httpserver.url_for("").rstrip("/"),
        sources_config_path=config_path,
    )

    assert result is None
