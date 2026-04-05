import functools
import io

import numpy as np
from PIL import Image
from rio_tiler.errors import EmptyMosaicError, TileOutsideBounds
from rio_tiler.io import COGReader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader


@functools.cache
def _violent_colormap() -> dict:
    """Design system colormap for violent crime: linen-100 → rouge-500 → rouge-700.

    0      → transparent (no crime data)
    1-255  → linen-100 (#F8F5F0) through rouge-500 (#B85450) to rouge-700 (#8B2E2B)
    """
    stops = [
        (248, 245, 240),  # linen-100
        (184, 84, 80),    # rouge-500 (#B85450)
        (139, 46, 43),    # rouge-700 (#8B2E2B)
    ]
    colormap: dict = {0: (0, 0, 0, 0)}
    for i in range(1, 256):
        t = (i - 1) / 254.0
        if t <= 0.5:
            s = t / 0.5
            r0, g0, b0 = stops[0]
            r1, g1, b1 = stops[1]
        else:
            s = (t - 0.5) / 0.5
            r0, g0, b0 = stops[1]
            r1, g1, b1 = stops[2]
        colormap[i] = (round(r0 + s * (r1 - r0)), round(g0 + s * (g1 - g0)), round(b0 + s * (b1 - b0)), 255)
    return colormap


@functools.cache
def _crime_colormap() -> dict:
    """Design system colormap: linen-100 → bronze-400 → ink-700.

    0      → transparent (no crime data)
    1-255  → linen-100 (#F8F5F0) through bronze-400 (#B89A78) to ink-700 (#3E3B37)
    """
    stops = [
        (248, 245, 240),  # linen-100
        (184, 154, 120),  # bronze-400
        (62, 59, 55),     # ink-700
    ]
    colormap: dict = {0: (0, 0, 0, 0)}
    for i in range(1, 256):
        t = (i - 1) / 254.0
        if t <= 0.5:
            s = t / 0.5
            r0, g0, b0 = stops[0]
            r1, g1, b1 = stops[1]
        else:
            s = (t - 0.5) / 0.5
            r0, g0, b0 = stops[1]
            r1, g1, b1 = stops[2]
        colormap[i] = (round(r0 + s * (r1 - r0)), round(g0 + s * (g1 - g0)), round(b0 + s * (b1 - b0)), 255)
    return colormap


@functools.cache
def _render_empty_tile() -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _tile_reader(asset: str, x: int, y: int, z: int) -> ImageData:
    with COGReader(asset) as src:
        return src.tile(x, y, z)


def _render_float_tile(img: ImageData, colormap: dict) -> bytes:
    if img.data.dtype == np.float32:
        img = ImageData(np.clip(img.data * 255, 0, 255).astype(np.uint8), img.mask)
    return img.render("PNG", colormap=colormap)


def _sync_get_tile(vsi_paths: list[str], z: int, x: int, y: int, colormap: dict) -> bytes:
    try:
        img, _ = mosaic_reader(vsi_paths, _tile_reader, x, y, z)
        return _render_float_tile(img, colormap)
    except (EmptyMosaicError, TileOutsideBounds):
        return _render_empty_tile()


