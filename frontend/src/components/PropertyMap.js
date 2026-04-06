import React, { useEffect, useRef } from 'react';
import { Map, Marker, Source, Layer } from 'react-map-gl/mapbox';
import { MapPin } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';
import useLayers from '../hooks/useLayers';
import MapLayerControls from './MapLayerControls';
import CrimeLayerLegend from './CrimeLayerLegend';

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

const defaultViewState = { longitude: -122.4194, latitude: 37.7749, zoom: 10 };

function PropertyMap({ properties, onPropertySelect, selectedProperty }) {
  const mapRef = useRef(null);
  const { groups, isActive, toggle } = useLayers(
    selectedProperty?.county_fips ?? null,
  );

  const hasLayers = groups.flatMap((g) => g.categories).length > 0;

  const activeCategory =
    groups.flatMap((g) => g.categories).find((c) => isActive(c.id)) ?? null;

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
  }, [selectedProperty?.id, selectedProperty?.latitude, selectedProperty?.longitude]);

  return (
    <div className="relative w-full h-full">
      <Map
        ref={mapRef}
        initialViewState={defaultViewState}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/light-v11"
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
                style={{ cursor: 'pointer' }}
              >
                <MapPin
                  size={isSelected ? 32 : 22}
                  className={isSelected ? 'text-bronze-600' : 'text-bronze-400'}
                  strokeWidth={isSelected ? 2 : 1.5}
                  aria-label={isSelected ? 'Selected property' : 'Property'}
                />
              </Marker>
            );
          })}

        {selectedProperty?.county_polygon && (
          <Source type="geojson" data={selectedProperty.county_polygon}>
            <Layer
              type="line"
              paint={{ 'line-color': '#92400e', 'line-width': 2 }}
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
            <Layer type="raster" paint={{ 'raster-resampling': 'linear' }} />
          </Source>
        )}
      </Map>

      {hasLayers && (
        <>
          <MapLayerControls groups={groups} isActive={isActive} onToggle={toggle} />
          <CrimeLayerLegend groups={groups} isActive={isActive} panelOpen={!!selectedProperty} />
        </>
      )}
    </div>
  );
}

export default PropertyMap;
