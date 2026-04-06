import React, { useEffect, useRef } from "react";
import { Map, Marker } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
const DEFAULT_ZOOM = 18;

const MapComponent = ({ center }) => {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || !center) return;
    mapRef.current.flyTo({
      center: [center.lng, center.lat],
      zoom: DEFAULT_ZOOM,
    });
  }, [center]);

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: center?.lng ?? 0,
        latitude: center?.lat ?? 0,
        zoom: DEFAULT_ZOOM,
      }}
      style={{ width: "100%", height: "400px" }}
      mapStyle="mapbox://styles/mapbox/satellite-v9"
      mapboxAccessToken={MAPBOX_TOKEN}
      projection="mercator"
    >
      {center && <Marker longitude={center.lng} latitude={center.lat} />}
    </Map>
  );
};

export default MapComponent;
