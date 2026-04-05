from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from backend.services import crime_layer as cl


@pytest.fixture(autouse=True)
def clear_caches():
    cl._render_empty_tile.cache_clear()
    cl._crime_colormap.cache_clear()
    cl._violent_colormap.cache_clear()
    yield
    cl._render_empty_tile.cache_clear()
    cl._crime_colormap.cache_clear()
    cl._violent_colormap.cache_clear()


def test_render_empty_tile_is_256x256_png():
    tile_bytes = cl._render_empty_tile()
    img = Image.open(BytesIO(tile_bytes))
    assert img.size == (256, 256)
    assert img.format == "PNG"


def test_render_empty_tile_is_fully_transparent():
    tile_bytes = cl._render_empty_tile()
    img = Image.open(BytesIO(tile_bytes)).convert("RGBA")
    pixels = list(img.getdata())
    assert all(a == 0 for _, _, _, a in pixels)


def test_tile_reader_does_not_pass_tilesize():
    mock_src = MagicMock()
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_src)
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("backend.services.crime_layer.COGReader", return_value=mock_cm):
        cl._tile_reader("/vsis3/bucket/layer/region/latest.tif", x=10, y=20, z=5)

    mock_src.tile.assert_called_once_with(10, 20, 5)
