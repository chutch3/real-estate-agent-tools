import React, { useState, useEffect, useRef } from "react";
import { Map, Marker, Source, Layer } from "react-map-gl/mapbox";
import { MapPin } from "lucide-react";
import "mapbox-gl/dist/mapbox-gl.css";
import useLayers from "../hooks/useLayers";
import MapLayerControls from "./MapLayerControls";
import CrimeLayerLegend from "./CrimeLayerLegend";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

const defaultViewState = { longitude: -122.4194, latitude: 37.7749, zoom: 10 };

function PropertyMap({ properties, onPropertySelect, selectedProperty }) {
  const mapRef = useRef(null);
  const [isSatellite, setIsSatellite] = useState(false);
  const { groups, isActive, toggle } = useLayers(
    selectedProperty?.county_fips ?? null,
  );

  const hasLayers = groups.flatMap((g) => g.categories).length > 0;

  const activeCategory =
    groups.flatMap((g) => g.categories).find((c) => isActive(c.id)) ?? null;

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      if (!mapRef.current) return;
      mapRef.current.flyTo({
        center: [position.coords.longitude, position.coords.latitude],
        zoom: 11,
      });
    });
  }, []);

  useEffect(() => {
    if (
      !mapRef.current ||
      !selectedProperty?.latitude ||
      !selectedProperty?.longitude
    )
      return;
    mapRef.current.flyTo({
      center: [selectedProperty.longitude, selectedProperty.latitude],
      zoom: 14,
    });
  }, [
    selectedProperty?.id,
    selectedProperty?.latitude,
    selectedProperty?.longitude,
  ]);

  return (
    <div className="relative w-full h-full">
      <button
        onClick={() => setIsSatellite(!isSatellite)}
        className="absolute bottom-12 left-4 z-10 bg-white rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 focus:outline-none overflow-hidden group border-2 border-white w-24 h-24 flex items-end"
        aria-label="Toggle satellite view"
      >
        <div className="absolute inset-0 transition-transform duration-300 transform group-hover:scale-110">
          <img
            src={
              isSatellite
                ? "https://api.mapbox.com/styles/v1/mapbox/light-v11/static/-122.4194,37.7749,10,0/200x200?access_token=" +
                  MAPBOX_TOKEN
                : "https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/static/-122.4194,37.7749,10,0/200x200?access_token=" +
                  MAPBOX_TOKEN
            }
            alt={isSatellite ? "Map view" : "Satellite view"}
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative w-full bg-white/90 font-semibold text-xs py-1 text-center text-gray-800">
          {isSatellite ? "Map" : "Satellite"}
        </div>
      </button>

      <Map
        ref={mapRef}
        initialViewState={defaultViewState}
        style={{ width: "100%", height: "100%" }}
        mapStyle={
          isSatellite
            ? "mapbox://styles/mapbox/satellite-streets-v12"
            : "mapbox://styles/mapbox/light-v11"
        }
        mapboxAccessToken={MAPBOX_TOKEN}
        projection="mercator"
      >
        {properties
          .filter((p) => p.latitude !== 0 || p.longitude !== 0)
          .map((property) => {
            const isSelected = selectedProperty?.id === property.id;
            return (
              <Marker
                key={property.id}
                longitude={property.longitude}
                latitude={property.latitude}
                anchor="bottom"
                onClick={() => onPropertySelect(property)}
                style={{ cursor: "pointer" }}
              >
                <MapPin
                  size={isSelected ? 32 : 22}
                  className={isSelected ? "text-bronze-600" : "text-bronze-400"}
                  strokeWidth={isSelected ? 2 : 1.5}
                  aria-label={isSelected ? "Selected property" : "Property"}
                />
              </Marker>
            );
          })}

        {selectedProperty?.county_polygon && (
          <Source type="geojson" data={selectedProperty.county_polygon}>
            <Layer
              type="line"
              paint={{ "line-color": "#92400e", "line-width": 2 }}
            />
          </Source>
        )}

        {selectedProperty?.parcel_polygon && (
          <Source
            id="parcel-boundary"
            type="geojson"
            data={selectedProperty.parcel_polygon}
          >
            <Layer
              type="line"
              paint={{ "line-color": "#2563eb", "line-width": 2 }}
            />
          </Source>
        )}

        {activeCategory && (
          <Source
            id="active-layer"
            type="raster"
            tiles={[
              `${API_BASE_URL}/layers/${activeCategory.id}/tiles/{z}/{x}/{y}`,
            ]}
            tileSize={256}
            maxzoom={activeCategory.tile_zoom ?? 12}
            bounds={activeCategory.bbox ?? undefined}
          >
            <Layer type="raster" paint={{ "raster-resampling": "linear" }} />
          </Source>
        )}
      </Map>

      {hasLayers && (
        <>
          <MapLayerControls
            groups={groups}
            isActive={isActive}
            onToggle={toggle}
          />
          <CrimeLayerLegend
            groups={groups}
            isActive={isActive}
            panelOpen={!!selectedProperty}
          />
        </>
      )}
    </div>
  );
}

export default PropertyMap;
