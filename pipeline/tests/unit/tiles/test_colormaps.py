import pytest

from pipeline.tiles.colormaps import property_colormap, violent_colormap


class TestViolentColormap:
    @pytest.fixture
    def subject(self) -> dict:
        violent_colormap.cache_clear()
        return violent_colormap()

    def test_has_256_entries(self, subject):
        assert len(subject) == 256

    def test_zero_is_transparent(self, subject):
        assert subject[0] == (0, 0, 0, 0)

    def test_nonzero_entries_are_fully_opaque(self, subject):
        for i in range(1, 256):
            assert subject[i][3] == 255, f"Entry {i} should be opaque"

    def test_starts_at_linen_100(self, subject):
        r, g, b, _ = subject[1]
        assert (r, g, b) == (248, 245, 240)

    def test_ends_at_rouge_700(self, subject):
        r, g, b, _ = subject[255]
        assert (r, g, b) == (139, 46, 43)


class TestPropertyColormap:
    @pytest.fixture
    def subject(self) -> dict:
        property_colormap.cache_clear()
        return property_colormap()

    def test_has_256_entries(self, subject):
        assert len(subject) == 256

    def test_zero_is_transparent(self, subject):
        assert subject[0] == (0, 0, 0, 0)

    def test_starts_at_linen_100(self, subject):
        r, g, b, _ = subject[1]
        assert (r, g, b) == (248, 245, 240)

    def test_ends_at_ink_700(self, subject):
        r, g, b, _ = subject[255]
        assert (r, g, b) == (62, 59, 55)
