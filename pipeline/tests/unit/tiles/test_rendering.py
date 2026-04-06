import io

import morecantile
import numpy as np
import pytest
from PIL import Image
from shapely.geometry import box

from pipeline.tiles.rendering import render_png_tile, tiles_for_polygon

_TMS = morecantile.tms.get("WebMercatorQuad")
_LOUISVILLE_POLYGON = box(-86.035, 37.997, -85.404, 38.375)
_TILE_PX = 256


def _make_cog_bytes(polygon=_LOUISVILLE_POLYGON, value: float = 0.5) -> bytes:
    """Return a minimal float32 COG in EPSG:3857 covering the given polygon."""
    import os
    import tempfile

    import rasterio
    from pyproj import Transformer
    from rasterio.crs import CRS
    from rasterio.transform import from_bounds
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles
    from shapely.ops import transform as shapely_transform

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    poly_3857 = shapely_transform(transformer.transform, polygon)
    minx, miny, maxx, maxy = poly_3857.bounds

    src_fd, src_path = tempfile.mkstemp(suffix=".tif")
    os.close(src_fd)
    cog_fd, cog_path = tempfile.mkstemp(suffix=".tif")
    os.close(cog_fd)

    try:
        transform = from_bounds(minx, miny, maxx, maxy, 10, 10)
        with rasterio.open(
            src_path,
            "w",
            driver="GTiff",
            height=10,
            width=10,
            count=1,
            dtype="float32",
            crs=CRS.from_epsg(3857),
            transform=transform,
        ) as dst:
            dst.write(np.full((10, 10), value, dtype="float32"), 1)

        cog_translate(src_path, cog_path, cog_profiles.get("deflate"), quiet=True)
        with open(cog_path, "rb") as f:
            return f.read()
    finally:
        for path in (src_path, cog_path):
            if os.path.exists(path):
                os.unlink(path)


def _open_png(png_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png_bytes))


def test_tiles_for_polygon_returns_zoom12_tiles():
    tiles = tiles_for_polygon(_LOUISVILLE_POLYGON)

    assert len(tiles) > 0
    for tile in tiles:
        assert tile.z == 12


def test_tiles_for_polygon_all_intersect_polygon():
    tiles = tiles_for_polygon(_LOUISVILLE_POLYGON)

    for tile in tiles:
        bounds = _TMS.bounds(tile)
        tile_poly = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        assert tile_poly.intersects(_LOUISVILLE_POLYGON)


def test_render_png_tile_returns_256x256_rgba_png():
    cog_bytes = _make_cog_bytes()
    tiles = tiles_for_polygon(_LOUISVILLE_POLYGON)
    tile = tiles[0]

    png_bytes = render_png_tile(
        tile=tile,
        cog_bytes=cog_bytes,
        county_polygon=_LOUISVILLE_POLYGON,
        colormap={i: (i, 0, 0, 255) if i > 0 else (0, 0, 0, 0) for i in range(256)},
    )

    img = _open_png(png_bytes)
    assert img.format == "PNG"
    assert img.mode == "RGBA"
    assert img.size == (_TILE_PX, _TILE_PX)


def test_render_png_tile_pixels_outside_county_are_transparent():
    # Small polygon in one corner of Louisville bbox — tiles at the edge should
    # have significant transparent area
    small_polygon = box(-86.035, 37.997, -85.9, 38.05)
    cog_bytes = _make_cog_bytes(polygon=small_polygon, value=1.0)
    tiles = tiles_for_polygon(small_polygon)
    tile = tiles[0]

    bounds = _TMS.bounds(tile)
    tile_poly = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
    # Only use this test if the tile is a border tile (not fully inside the small polygon)
    if tile_poly.within(small_polygon):
        pytest.skip("Tile is fully inside polygon, skip border test")

    colormap = {i: (255, 0, 0, 255) if i > 0 else (0, 0, 0, 0) for i in range(256)}
    png_bytes = render_png_tile(
        tile=tile,
        cog_bytes=cog_bytes,
        county_polygon=small_polygon,
        colormap=colormap,
    )

    img = _open_png(png_bytes).convert("RGBA")
    pixels = np.array(img)
    alpha = pixels[:, :, 3]
    assert (alpha == 0).any(), "Expected some transparent pixels outside county polygon"


def test_render_png_tile_with_zero_data_returns_transparent():
    cog_bytes = _make_cog_bytes(value=0.0)
    tiles = tiles_for_polygon(_LOUISVILLE_POLYGON)
    tile = tiles[0]
    colormap = {0: (0, 0, 0, 0), **{i: (255, 0, 0, 255) for i in range(1, 256)}}

    png_bytes = render_png_tile(
        tile=tile,
        cog_bytes=cog_bytes,
        county_polygon=_LOUISVILLE_POLYGON,
        colormap=colormap,
    )

    img = _open_png(png_bytes).convert("RGBA")
    pixels = np.array(img)
    assert (pixels[:, :, 3] == 0).all(), "All pixels should be transparent for zero-value COG"
