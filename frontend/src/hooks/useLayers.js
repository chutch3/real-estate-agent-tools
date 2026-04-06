import { useState, useEffect } from "react";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

function useLayers(countyFips) {
  const [groups, setGroups] = useState([]);
  const [activeLayerIds, setActiveLayerIds] = useState(new Set());

  useEffect(() => {
    if (!countyFips) {
      setGroups([]);
      setActiveLayerIds(new Set());
      return;
    }
    fetch(`${API_BASE_URL}/layers?county_fips=${countyFips}`)
      .then((r) => r.json())
      .then((data) => {
        setGroups(data.groups || []);
        setActiveLayerIds(new Set());
      })
      .catch(() => {});
  }, [countyFips]);

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
