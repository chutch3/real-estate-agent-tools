import functools


def _interpolate_stops(stops: list[tuple[int, int, int]]) -> dict[int, tuple[int, int, int, int]]:
    """Build a 256-entry colormap from a list of RGB stops.

    Index 0 → transparent. Indices 1-255 → interpolated through the stops.
    """
    colormap: dict[int, tuple[int, int, int, int]] = {0: (0, 0, 0, 0)}
    n_stops = len(stops)
    for i in range(1, 256):
        t = (i - 1) / 254.0
        segment = t * (n_stops - 1)
        lo = int(segment)
        hi = min(lo + 1, n_stops - 1)
        s = segment - lo
        r0, g0, b0 = stops[lo]
        r1, g1, b1 = stops[hi]
        colormap[i] = (
            round(r0 + s * (r1 - r0)),
            round(g0 + s * (g1 - g0)),
            round(b0 + s * (b1 - b0)),
            255,
        )
    return colormap


@functools.cache
def violent_colormap() -> dict[int, tuple[int, int, int, int]]:
    """linen-100 → rouge-500 → rouge-700."""
    return _interpolate_stops([
        (248, 245, 240),  # linen-100
        (184, 84, 80),    # rouge-500
        (139, 46, 43),    # rouge-700
    ])


@functools.cache
def property_colormap() -> dict[int, tuple[int, int, int, int]]:
    """linen-100 → bronze-400 → ink-700."""
    return _interpolate_stops([
        (248, 245, 240),  # linen-100
        (184, 154, 120),  # bronze-400
        (62, 59, 55),     # ink-700
    ])


LAYER_COLORMAPS: dict[str, callable] = {
    "crime-violent": violent_colormap,
    "crime-property": property_colormap,
}
