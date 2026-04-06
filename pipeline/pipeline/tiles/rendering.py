import io

import morecantile
import numpy as np
from PIL import Image
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.enums import Resampling
from rasterio.windows import from_bounds as window_from_bounds
from shapely.geometry import box as shapely_box, mapping
from shapely.ops import transform as shapely_transform
from shapely.geometry import Polygon

_TMS = morecantile.tms.get("WebMercatorQuad")
BASE_ZOOM = 12
TILE_PX = 256

_WGS84_TO_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def tiles_for_polygon(polygon: Polygon) -> list[morecantile.Tile]:
    """Return all zoom-12 tiles that intersect the given WGS84 polygon."""
    minx, miny, maxx, maxy = polygon.bounds
    return list(_TMS.tiles(minx, miny, maxx, maxy, zooms=BASE_ZOOM))


def render_png_tile(
    tile: morecantile.Tile,
    cog_bytes: bytes,
    county_polygon: Polygon,
    colormap: dict[int, tuple[int, int, int, int]],
) -> bytes:
    """Render a 256x256 RGBA PNG tile from a COG, clipped to the county polygon."""
    xy_bounds = _TMS.xy_bounds(tile)

    with MemoryFile(cog_bytes) as memfile:
        with memfile.open() as src:
            window = window_from_bounds(
                xy_bounds.left, xy_bounds.bottom, xy_bounds.right, xy_bounds.top,
                src.transform,
            )
            data = src.read(
                1,
                window=window,
                out_shape=(TILE_PX, TILE_PX),
                resampling=Resampling.bilinear,
                boundless=True,
                fill_value=0.0,
            )

    county_poly_3857 = shapely_transform(_WGS84_TO_3857.transform, county_polygon)
    tile_poly_3857 = shapely_box(xy_bounds.left, xy_bounds.bottom, xy_bounds.right, xy_bounds.top)
    clip_polygon = county_poly_3857.intersection(tile_poly_3857)

    transform_3857 = transform_from_bounds(
        xy_bounds.left, xy_bounds.bottom, xy_bounds.right, xy_bounds.top,
        TILE_PX, TILE_PX,
    )

    if not clip_polygon.is_empty:
        outside_mask = geometry_mask(
            [mapping(clip_polygon)],
            out_shape=(TILE_PX, TILE_PX),
            transform=transform_3857,
        )
        data = data.copy()
        data[outside_mask] = 0.0
    else:
        data = np.zeros((TILE_PX, TILE_PX), dtype=np.float32)

    img_data = (np.clip(data, 0.0, 1.0) * 255).astype(np.uint8)

    colormap_array = np.array(
        [colormap.get(i, (0, 0, 0, 0)) for i in range(256)],
        dtype=np.uint8,
    )
    rgba = colormap_array[img_data]

    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return buf.getvalue()
