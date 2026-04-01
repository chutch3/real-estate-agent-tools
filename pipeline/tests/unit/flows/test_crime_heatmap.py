import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Point, box

from pipeline.flows.crime_heatmap import _compute_kde_grid

_POLYGON = box(-86.035, 37.997, -85.404, 38.375)

# Four clearly non-collinear points spanning the polygon
_NON_COLLINEAR = [(-85.75, 38.2), (-85.80, 38.1), (-85.70, 38.3), (-85.65, 38.15)]


def _make_records(*coords: tuple[float, float]) -> gpd.GeoDataFrame:
    rows = [
        {
            "lat": lat,
            "lon": lon,
            "category": "other",
            "date": "2025-01-01",
            "source": "test",
            "geometry": Point(lon, lat),
        }
        for lon, lat in coords
    ]
    if not rows:
        return gpd.GeoDataFrame(
            columns=["lat", "lon", "category", "date", "source", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def test_compute_kde_grid_returns_zeros_for_empty_records() -> None:
    records = _make_records()

    result = _compute_kde_grid(records, _POLYGON)

    assert result.values.sum() == pytest.approx(0.0)
    assert result.values.shape == (result.height, result.width)


def test_compute_kde_grid_returns_single_peak_for_one_record() -> None:
    records = _make_records((-85.75, 38.2))

    result = _compute_kde_grid(records, _POLYGON)

    assert result.values.max() == pytest.approx(1.0)
    assert result.values[result.height // 2, result.width // 2] == pytest.approx(1.0)


def test_compute_kde_grid_normalizes_to_one_for_non_collinear_records() -> None:
    records = _make_records(*_NON_COLLINEAR)

    result = _compute_kde_grid(records, _POLYGON)

    assert result.values.max() == pytest.approx(1.0, rel=1e-3)
    assert result.values.min() >= 0.0


def test_compute_kde_grid_returns_zeros_for_collinear_records() -> None:
    # Two points are always collinear in 2D — gaussian_kde cannot estimate bandwidth
    records = _make_records((-85.75, 38.2), (-85.80, 38.1))

    result = _compute_kde_grid(records, _POLYGON)

    assert result.values.sum() == pytest.approx(0.0)


def test_compute_kde_grid_returns_correct_bounds() -> None:
    records = _make_records(*_NON_COLLINEAR)

    result = _compute_kde_grid(records, _POLYGON)

    assert result.bounds == pytest.approx(_POLYGON.bounds)


def test_compute_kde_grid_grid_shape_matches_width_and_height() -> None:
    records = _make_records(*_NON_COLLINEAR)

    result = _compute_kde_grid(records, _POLYGON)

    assert result.values.shape == (result.height, result.width)
    assert result.width >= 10
    assert result.height >= 10
