import { useState, useEffect, useRef } from "react";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

export function tileIntersectsBbox(x, y, z, bbox) {
  const [minLon, minLat, maxLon, maxLat] = bbox;
  const n = Math.pow(2, z);
  const tileWest = (x / n) * 360 - 180;
  const tileEast = ((x + 1) / n) * 360 - 180;
  const tileNorth =
    (Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / n))) * 180) / Math.PI;
  const tileSouth =
    (Math.atan(Math.sinh(Math.PI * (1 - (2 * (y + 1)) / n))) * 180) / Math.PI;
  return (
    tileEast > minLon &&
    tileWest < maxLon &&
    tileNorth > minLat &&
    tileSouth < maxLat
  );
}

function useLayers(mapInstance, countyFips) {
  const [groups, setGroups] = useState([]);
  const [activeLayerIds, setActiveLayerIds] = useState(new Set());
  const bboxByLayerId = useRef(new Map());

  useEffect(() => {
    if (!countyFips) {
      setGroups([]);
      setActiveLayerIds(new Set());
      return;
    }
    fetch(`${API_BASE_URL}/layers?county_fips=${countyFips}`)
      .then((r) => r.json())
      .then((data) => {
        const fetchedGroups = data.groups || [];
        setGroups(fetchedGroups);
        setActiveLayerIds(new Set());
        const bboxMap = new Map();
        for (const group of fetchedGroups) {
          for (const category of group.categories || []) {
            if (category.bbox) {
              bboxMap.set(category.id, category.bbox);
            }
          }
        }
        bboxByLayerId.current = bboxMap;
      })
      .catch(() => {});
  }, [countyFips]);

  useEffect(() => {
    if (!mapInstance || !window.google?.maps) return;

    mapInstance.overlayMapTypes.clear();

    for (const group of groups) {
      for (const category of group.categories) {
        if (!activeLayerIds.has(category.id)) continue;
        const layerId = category.id;
        const overlay = new window.google.maps.ImageMapType({
          getTileUrl: (coord, zoom) => {
            const bbox = bboxByLayerId.current.get(layerId);
            if (bbox && !tileIntersectsBbox(coord.x, coord.y, zoom, bbox))
              return null;
            return `${API_BASE_URL}/layers/${layerId}/tiles/${zoom}/${coord.x}/${coord.y}`;
          },
          tileSize: new window.google.maps.Size(256, 256),
          maxZoom: 19,
          minZoom: 0,
          name: layerId,
        });
        mapInstance.overlayMapTypes.push(overlay);
      }
    }
  }, [groups, mapInstance, activeLayerIds]);

  const isActive = (id) => activeLayerIds.has(id);

  const toggle = (id) => {
    setActiveLayerIds((prev) => {
      if (prev.has(id)) {
        return new Set();
      }
      return new Set([id]);
    });
  };

  return { groups, isActive, toggle };
}

export default useLayers;
